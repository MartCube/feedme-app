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
from urllib.parse import urlsplit

import feedparser
import requests
from django.db import DataError, transaction
from django.db.models import Q
from django.utils import timezone

from . import icons, youtube
from .fetch import ALLOWED_SCHEMES, USER_AGENT, PageUnavailable, check_public, read_capped
from .models import Post, Source
from .retention import age_cutoff

ACCEPT = 'application/atom+xml,application/rss+xml,application/xml;q=0.9,*/*;q=0.8'
# (connect, read). Split so a dead host fails fast while a slow-but-alive one gets a chance.
TIMEOUT = (5, 15)
# The most a feed download may be. hnrss and Reddit serve tens of KB; an archive feed with
# every post since 2019 is under 1 MB. Past this the worker is holding a download, not a
# feed, in memory — and it is the worker, so nobody is watching it go.
MAX_FEED_BYTES = 10 * 1024 * 1024
# Post.summary is a TextField, but Post.search is a tsvector generated from it, and Postgres
# caps a tsvector at 1 MB — a description with enough distinct words fails the INSERT. The
# largest summary a real source has served is 15 KB (Reddit, a whole table of markup); this
# is four times that, and past it the field is no longer a summary of anything.
MAX_SUMMARY = 64 * 1024

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

    Guarded by core/fetch.py's address check and read cap — the same two extraction and
    discovery use — but not routed through its fetch_url: this call carries validators and
    has to hand back the response's status and headers, which fetch_url doesn't expose.
    Only the stored URL is vetted; requests follows redirects on its own, unchecked, since
    what a feed redirects to is parsed and stored, never handed back to a caller.
    """
    headers = {'user-agent': USER_AGENT, 'accept': ACCEPT}
    if source.etag:
        headers['if-none-match'] = source.etag
    if source.last_modified:
        headers['if-modified-since'] = source.last_modified

    check_public(source.feed_url)
    response = requests.get(source.feed_url, headers=headers, timeout=TIMEOUT, stream=True)
    with response:
        return FetchResult(
            status_code=response.status_code,
            body=read_capped(response, MAX_FEED_BYTES),
            content_type=response.headers.get('content-type', ''),
            etag=response.headers.get('etag', ''),
            last_modified=response.headers.get('last-modified', ''),
        )


def ingest_source(source):
    """Poll one source and upsert its posts. Never raises — failures are recorded."""
    now = timezone.now()

    try:
        fetched = fetch_feed(source)
    except (requests.RequestException, PageUnavailable) as exc:
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

    metadata = feed_metadata(parsed.feed)
    if not source.icon_url and not metadata['icon_url']:
        # Before the transaction, since it is a network call. Once per source in practice:
        # whatever comes back is stored, and a stored icon is never looked up again.
        site_url = _http_or_blank(metadata['site_url'] or source.site_url)
        metadata['icon_url'] = icons.site_icon(site_url)

    if source.type == Source.Type.YOUTUBE:
        # Also before the transaction: swapping in the bigger poster may take a request
        # per video, and each answer is cached, so a re-poll costs none (core/youtube.py).
        for entry in parsed.entries:
            for thumbnail in entry.get('media_thumbnail') or ():
                if thumbnail.get('url'):
                    thumbnail['url'] = youtube.poster(thumbnail['url'])

    # One transaction, so a worker killed mid-poll leaves nothing half-written: either the
    # whole batch and the new timestamps land, or none of it does and the next poll redoes
    # the work. The network call is already finished, so no lock is held across I/O.
    try:
        with transaction.atomic():
            created, updated = _upsert_posts(source, parsed.entries)
            _backfill_source_metadata(source, metadata)
            _record_success(source, now, fetched)
    except DataError as exc:
        # Content Postgres refuses — a NUL byte, a tsvector past its 1 MB cap. _entry_to_post
        # sanitises the cases we know, but whatever comes next must still be *this* source's
        # failure, on its own backoff ladder, rather than an exception the actor retries
        # three times and the sweep re-enqueues forever with error_count never moving.
        # Everything else still raises: a database blip is the worker's problem, not the feed's.
        return _record_failure(source, now, f'unstorable entry: {exc}'.strip())
    return IngestResult(OK, created=created, updated=updated)


def due_sources(now=None):
    """Active sources that have never been fetched or whose next_fetch_at has passed."""
    now = now or timezone.now()
    return Source.objects.filter(active=True).filter(
        Q(next_fetch_at__isnull=True) | Q(next_fetch_at__lte=now)
    )


def _upsert_posts(source, entries):
    """Create or update one post per entry — but never create what retention deletes tonight.

    An archive feed serves far more than a retention window: nuxt.com/blog/rss.xml carries
    every post back to 2019. Without this the two jobs fight over the same rows forever —
    the nightly prune deletes what is past the window, the next poll recreates it with a
    fresh uid and an empty article cache, and the table never actually gets lean. Found by
    running both against the real dev database, not by a test.

    An entry already in the table is still updated, so a saved post that has aged out of
    the window keeps tracking whatever its source now says about it.
    """
    created = updated = 0
    cutoff = age_cutoff()
    for entry in entries:
        guid, fields = _entry_to_post(entry)
        if guid is None:
            continue
        if fields['published_at'] < cutoff:
            updated += Post.objects.filter(source=source, guid=guid).update(**fields)
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
    link = _text(entry.get('link'))
    guid = _text(entry.get('id')) or link
    # a link that isn't http(s) is not a place a post can live, whatever the markup says —
    # and the reader will render post_url as an href, so `javascript:` never gets that far
    if not link or not guid or not _is_http(link):
        return None, None

    return guid[:500], {
        'title': (_text(entry.get('title')) or '(untitled)')[:500],
        'post_url': link[:1000],
        'image_url': _http_or_blank(_pick_image(entry))[:1000],
        # raw as given: HTML from a blog or Reddit, plain text from YouTube. The reader's
        # full article text is a separate field, extracted on demand in T10.
        'summary': _text(entry.get('summary'))[:MAX_SUMMARY],
        'published_at': _published_at(entry),
    }


def _text(value):
    """A string as Postgres will store it: NUL bytes gone, edges trimmed.

    A NUL is legal in the XML a feed serves and illegal in every text column we have — the
    one character that turns a valid entry into a DataError on the INSERT.
    """
    return (value or '').replace('\x00', '').strip()


def _is_http(url):
    return urlsplit(url).scheme in ALLOWED_SCHEMES


def _http_or_blank(url):
    """A URL the frontend may put in a src or href, or '' — the same allowlist core/fetch.py
    applies before it opens a socket, applied here before the value reaches a template."""
    return url if _is_http(url) else ''


def _pick_image(entry):
    """media:thumbnail (YouTube, some Reddit posts), then any image enclosure."""
    for thumbnail in entry.get('media_thumbnail') or ():
        if thumbnail.get('url'):
            return _full_size(thumbnail['url'])
    for media in entry.get('media_content') or ():
        if media.get('url') and media.get('type', '').startswith('image/'):
            return media['url']
    for link in entry.get('links') or ():
        if link.get('rel') == 'enclosure' and link.get('type', '').startswith('image/'):
            return link.get('href') or ''
    return ''


def _full_size(url):
    """The original behind a Reddit preview, which is what a post image should start from.

    Reddit's RSS hands out `preview.redd.it/<id>.jpeg?width=640&…` — 640px at best and 140
    as often, a size the post page stretches into a blur. The same file sits full size at
    `i.redd.it/<id>.jpeg`, and the proxy scales it down to whatever is asked for.
    `external-preview.redd.it` is a link's preview with no original behind it, so it stays.
    """
    parts = urlsplit(url)
    if parts.hostname != 'preview.redd.it':
        return url
    return f'https://i.redd.it{parts.path}'


def _published_at(entry):
    """feedparser normalises every date to a UTC struct_time, so this is safe.

    `published` before `updated`: YouTube bumps `updated` on view-count changes, which
    would otherwise reshuffle the timeline on every poll.

    Clamped to now: lists read newest-first, so a post dated in the future would head every
    one of them until that date arrives — and retention's age window would never reach it.
    """
    now = timezone.now()
    for key in ('published_parsed', 'updated_parsed'):
        parsed = entry.get(key)
        if parsed:
            return min(datetime(*parsed[:6], tzinfo=UTC), now)
    return now


def feed_metadata(feed):
    """A feed's own title, site and icon, as feedparser exposes them.

    Here rather than in core/discover.py, which reads the same three off the same parse to
    label a candidate: where a feed keeps its name is one rule, and a feed described
    differently in the add wizard than on the home screen would be a small, constant lie.
    """
    return {
        'title': feed.get('title') or '',
        'site_url': feed.get('link') or '',
        # Atom's <icon> only, which is square by definition. RSS's <image> and Atom's <logo>
        # are logos and banners, and a square crop of one reads worse than the site's own
        # icon, which core/icons.py finds instead (docs/images.md).
        'icon_url': feed.get('icon') or '',
    }


def _backfill_source_metadata(source, metadata):
    """Fill blank source fields from the feed itself — never overwrite what's set.

    Sources created by hand in admin (and, from T7, by subscribing to a bare URL) have
    only a feed_url; the feed knows its own title, site and icon.
    """
    for field, value in metadata.items():
        value = _text(value)
        if field != 'title':
            # site_url and icon_url end up in an href and an <img src> on the home screen
            value = _http_or_blank(value)
        if not getattr(source, field) and value:
            # each column has its own limit (title is 300, the URLs are 500) and a feed
            # is free to hand us something longer
            setattr(source, field, value[: Source._meta.get_field(field).max_length])


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
