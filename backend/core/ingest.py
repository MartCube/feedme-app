"""Fetch one source's feed and upsert its posts.

A plain synchronous function on purpose, and still one now that T9's actor wraps it
(core/tasks.py): it stays callable from a test, a shell and a management command with no
broker running, and `POST /feeds` calls it inline because that fetch is what proves a
pasted URL is a feed at all.

`requests` does the HTTP, feedparser only parses. feedparser can fetch a URL itself, but
that path passes no timeout to urllib — a hung server would block forever, and the only
lever is the process-global `socket.setdefaulttimeout()`. Upstream has removed those HTTP
arguments from `parse()` for feedparser 7 and points callers here anyway.
"""

import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import feedparser
import requests
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import Post, Source

USER_AGENT = 'FeedMe/1.0 (+https://github.com/MartCube/feedme-app)'
ACCEPT = 'application/atom+xml,application/rss+xml,application/xml;q=0.9,*/*;q=0.8'
# (connect, read). Split so a dead host fails fast while a slow-but-alive one gets a chance.
TIMEOUT = (5, 15)

POLL_INTERVAL = timedelta(minutes=30)
# ±10% so a batch of sources created together doesn't come due in the same sweep forever
POLL_JITTER = 0.1
MAX_BACKOFF = timedelta(hours=24)
# after this many consecutive failures the source is deactivated; the admin action
# "Reset errors and poll on the next run" is how you bring one back
MAX_FAILURES = 5

OK = 'ok'
NOT_MODIFIED = 'not_modified'
ERROR = 'error'


@dataclass(frozen=True)
class FetchResult:
    """What the network gave us, with nothing feedparser-shaped about it."""

    status_code: int
    body: bytes = b''
    content_type: str = ''
    etag: str = ''
    last_modified: str = ''


@dataclass(frozen=True)
class IngestResult:
    status: str
    created: int = 0
    updated: int = 0
    detail: str = ''

    def __str__(self):
        if self.status == OK:
            return f'ok — {self.created} new, {self.updated} updated'
        if self.status == NOT_MODIFIED:
            return 'not modified'
        return f'error — {self.detail}'


def fetch_feed(source):
    """The only place ingest touches the network. Tests replace this wholesale.

    Conditional GET: the stored etag / last_modified are opaque strings we hand straight
    back, so a server that supports them answers 304 with an empty body. Most polls are
    that cheap — it's what makes polling hundreds of sources affordable.
    """
    headers = {'user-agent': USER_AGENT, 'accept': ACCEPT}
    if source.etag:
        headers['if-none-match'] = source.etag
    if source.last_modified:
        headers['if-modified-since'] = source.last_modified

    response = requests.get(source.feed_url, headers=headers, timeout=TIMEOUT)
    return FetchResult(
        status_code=response.status_code,
        body=response.content,
        content_type=response.headers.get('content-type', ''),
        etag=response.headers.get('etag', ''),
        last_modified=response.headers.get('last-modified', ''),
    )


def ingest_source(source):
    """Poll one source and upsert its posts. Never raises — failures are recorded."""
    now = timezone.now()

    try:
        fetched = fetch_feed(source)
    except requests.RequestException as exc:
        return _record_failure(source, now, f'{type(exc).__name__}: {exc}')

    if fetched.status_code == 304:
        # nothing to parse, and the validators we sent are still the current ones
        _record_success(source, now)
        return IngestResult(NOT_MODIFIED)

    if fetched.status_code >= 400:
        return _record_failure(source, now, f'HTTP {fetched.status_code}')

    parsed = feedparser.parse(
        fetched.body,
        # content-type keeps feedparser's charset detection working on raw bytes;
        # content-location gives it a base for resolving relative links
        response_headers={
            'content-type': fetched.content_type,
            'content-location': source.feed_url,
        },
    )
    # bozo alone isn't fatal — feedparser recovers entries from feeds that are merely
    # sloppy, which is most of them. No entries at all is what means "this isn't a feed".
    if not parsed.entries:
        return _record_failure(source, now, _describe_empty(parsed))

    # One transaction, so a worker killed mid-poll leaves nothing half-written: either the
    # whole batch and the new timestamps land, or none of it does and the next poll redoes
    # the work. The network call is already finished, so no lock is held across I/O.
    with transaction.atomic():
        created, updated = _upsert_posts(source, parsed.entries)
        _backfill_source_metadata(source, parsed.feed)
        _record_success(source, now, fetched)
    return IngestResult(OK, created=created, updated=updated)


def due_sources(now=None):
    """Active sources that have never been fetched or whose next_fetch_at has passed."""
    now = now or timezone.now()
    return Source.objects.filter(active=True).filter(
        Q(next_fetch_at__isnull=True) | Q(next_fetch_at__lte=now)
    )


def _upsert_posts(source, entries):
    created = updated = 0
    for entry in entries:
        guid, fields = _entry_to_post(entry)
        if guid is None:
            continue
        _, was_created = Post.objects.update_or_create(source=source, guid=guid, defaults=fields)
        if was_created:
            created += 1
        else:
            updated += 1
    return created, updated


def _entry_to_post(entry):
    """Map one feedparser entry onto Post fields, or (None, None) to skip it.

    `id` is feedparser's normalised <guid> / Atom <id> — a real identifier on all three
    source types (`yt:video:…`, Reddit's `t3_…` URL, the blog's permalink). Falling back
    to the link keeps feeds that omit it working.
    """
    link = (entry.get('link') or '').strip()
    guid = (entry.get('id') or link).strip()
    if not link or not guid:
        return None, None

    return guid[:500], {
        'title': (entry.get('title') or '(untitled)').strip()[:500],
        'post_url': link[:1000],
        'image_url': _pick_image(entry)[:1000],
        # raw as given: HTML from a blog or Reddit, plain text from YouTube. The reader's
        # full article text is a separate field, extracted on demand in T10.
        'summary': entry.get('summary') or '',
        'published_at': _published_at(entry),
    }


def _pick_image(entry):
    """media:thumbnail (YouTube, some Reddit posts), then any image enclosure."""
    for thumbnail in entry.get('media_thumbnail') or ():
        if thumbnail.get('url'):
            return thumbnail['url']
    for media in entry.get('media_content') or ():
        if media.get('url') and media.get('type', '').startswith('image/'):
            return media['url']
    for link in entry.get('links') or ():
        if link.get('rel') == 'enclosure' and link.get('type', '').startswith('image/'):
            return link.get('href') or ''
    return ''


def _published_at(entry):
    """feedparser normalises every date to a UTC struct_time, so this is safe.

    `published` before `updated`: YouTube bumps `updated` on view-count changes, which
    would otherwise reshuffle the timeline on every poll.
    """
    for key in ('published_parsed', 'updated_parsed'):
        parsed = entry.get(key)
        if parsed:
            return datetime(*parsed[:6], tzinfo=UTC)
    return timezone.now()


def _backfill_source_metadata(source, feed):
    """Fill blank source fields from the feed itself — never overwrite what's set.

    Sources created by hand in admin (and, from T7, by subscribing to a bare URL) have
    only a feed_url; the feed knows its own title, site and icon.
    """
    icon = feed.get('icon') or feed.get('logo') or (feed.get('image') or {}).get('href') or ''
    for field, value in (
        ('title', feed.get('title') or ''),
        ('site_url', feed.get('link') or ''),
        ('icon_url', icon),
    ):
        if not getattr(source, field) and value:
            # each column has its own limit (title is 300, the URLs are 500) and a feed
            # is free to hand us something longer
            setattr(source, field, value.strip()[: Source._meta.get_field(field).max_length])


def _describe_empty(parsed):
    exception = parsed.get('bozo_exception')
    return f'no entries ({type(exception).__name__})' if exception else 'no entries'


def _record_success(source, now, fetched=None):
    fields = ['error_count', 'last_fetched_at', 'next_fetch_at']
    source.error_count = 0
    source.last_fetched_at = now
    source.next_fetch_at = now + POLL_INTERVAL * random.uniform(1 - POLL_JITTER, 1 + POLL_JITTER)
    if fetched is not None:
        # only on a 200: a 304 sends no validators, and blanking them would turn every
        # subsequent poll into a full download. Same reason the backfilled metadata is
        # written here — on a 304 there was no feed to read it from.
        source.etag = fetched.etag[:200]
        source.last_modified = fetched.last_modified[:100]
        fields += ['etag', 'last_modified', 'title', 'site_url', 'icon_url']
    source.save(update_fields=fields)


def _record_failure(source, now, detail):
    """Back off exponentially, and stop polling a source that has stopped answering.

    last_fetched_at is deliberately left alone — it stays "when data last arrived", so a
    stale timestamp next to a rising error_count reads correctly in admin.
    """
    source.error_count += 1
    backoff = min(POLL_INTERVAL * 2**source.error_count, MAX_BACKOFF)
    source.next_fetch_at = now + backoff
    fields = ['error_count', 'next_fetch_at']
    if source.error_count >= MAX_FAILURES:
        source.active = False
        fields.append('active')
    source.save(update_fields=fields)
    return IngestResult(ERROR, detail=detail)
