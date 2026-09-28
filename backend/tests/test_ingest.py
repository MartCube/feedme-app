from datetime import timedelta
from io import StringIO

import pytest
import requests
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from core import icons, ingest
from core.ingest import (
    ERROR,
    MAX_FAILURES,
    NOT_MODIFIED,
    OK,
    POLL_INTERVAL,
    FetchResult,
    due_sources,
    ingest_source,
)
from core.models import Post, Source
from tests import feeds


@pytest.fixture
def source(db):
    return Source.objects.create(
        type=Source.Type.WEBSITE, feed_url='https://medium.com/feed/tag/vuejs'
    )


def ok(body, etag='', last_modified=''):
    return FetchResult(
        status_code=200,
        body=body,
        content_type='application/rss+xml; charset=utf-8',
        etag=etag,
        last_modified=last_modified,
    )


def serve(monkeypatch, *outcomes):
    """Replace the one network call. Each poll takes the next outcome; the last repeats.

    An Exception in the list is raised rather than returned, which is how a connection
    failure reaches ingest_source.
    """
    queue = list(outcomes)

    def fetch(source):
        outcome = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(ingest, 'fetch_feed', fetch)


def test_a_first_poll_creates_posts(source, monkeypatch):
    serve(monkeypatch, ok(feeds.RSS_BLOG))

    result = ingest_source(source)

    assert (result.status, result.created, result.updated) == (OK, 2, 0)
    post = Post.objects.get(guid='https://medium.com/p/one')
    assert post.title == 'The Composition API'
    assert post.post_url == 'https://medium.com/p/one?source=rss'
    assert post.summary == '<p>Why script setup is the cleanest way</p>'
    assert post.published_at.isoformat() == '2026-08-24T20:36:01+00:00'
    assert post.uid.startswith('post_')


def test_a_repoll_of_an_unchanged_feed_creates_no_duplicates(source, monkeypatch):
    serve(monkeypatch, ok(feeds.RSS_BLOG))

    ingest_source(source)
    result = ingest_source(source)

    assert (result.created, result.updated) == (0, 2)
    assert Post.objects.count() == 2


def test_a_repoll_updates_changed_entries_and_adds_new_ones(source, monkeypatch):
    serve(monkeypatch, ok(feeds.RSS_BLOG), ok(feeds.RSS_BLOG_UPDATED))
    ingest_source(source)

    result = ingest_source(source)

    assert (result.created, result.updated) == (1, 2)
    assert Post.objects.count() == 3
    assert Post.objects.get(guid='https://medium.com/p/one').title == (
        'The Composition API, revised'
    )


def test_a_repoll_keeps_the_uid_of_an_updated_post(source, monkeypatch):
    """The uid is the frontend's handle on a post — an upsert must not mint a new one."""
    serve(monkeypatch, ok(feeds.RSS_BLOG), ok(feeds.RSS_BLOG_UPDATED))
    ingest_source(source)
    uid = Post.objects.get(guid='https://medium.com/p/one').uid

    ingest_source(source)

    assert Post.objects.get(guid='https://medium.com/p/one').uid == uid


def test_the_response_validators_are_stored(source, monkeypatch):
    serve(
        monkeypatch, ok(feeds.RSS_BLOG, etag='"abc"', last_modified='Mon, 24 Aug 2026 20:36:01 GMT')
    )

    ingest_source(source)

    source.refresh_from_db()
    assert source.etag == '"abc"'
    assert source.last_modified == 'Mon, 24 Aug 2026 20:36:01 GMT'


def test_a_304_is_a_no_op_that_keeps_the_validators(source, monkeypatch):
    serve(monkeypatch, ok(feeds.RSS_BLOG, etag='"abc"'), FetchResult(status_code=304))
    ingest_source(source)

    result = ingest_source(source)

    assert result.status == NOT_MODIFIED
    assert Post.objects.count() == 2
    source.refresh_from_db()
    # blanking the etag here would turn every later poll into a full download
    assert source.etag == '"abc"'
    assert source.error_count == 0
    assert source.next_fetch_at > timezone.now()


def test_the_stored_validators_are_sent_on_the_next_poll(source, monkeypatch):
    """fetch_feed is the seam every other test replaces — this is the test of the seam.

    A literal public address, as tests/test_fetch.py uses: fetch_feed vets the URL before
    the GET, and a hostname would drag a resolver into the test."""
    from tests.test_fetch import FakeResponse

    source.feed_url = 'http://93.184.216.34/rss'
    source.etag = '"abc"'
    source.last_modified = 'Mon, 24 Aug 2026 20:36:01 GMT'
    sent = {}

    def fake_get(url, headers, timeout, stream):
        sent.update(url=url, headers=headers, timeout=timeout)
        return FakeResponse(304)

    monkeypatch.setattr(ingest.requests, 'get', fake_get)
    ingest.fetch_feed(source)

    assert sent['headers']['if-none-match'] == '"abc"'
    assert sent['headers']['if-modified-since'] == 'Mon, 24 Aug 2026 20:36:01 GMT'
    assert sent['headers']['user-agent'].startswith('FeedMe/')
    assert sent['timeout'] == ingest.TIMEOUT


def test_no_validators_are_sent_when_none_are_stored(source, monkeypatch):
    from tests.test_fetch import FakeResponse

    source.feed_url = 'http://93.184.216.34/rss'
    sent = {}

    def fake_get(url, headers, timeout, stream):
        sent.update(headers=headers)
        return FakeResponse(200, chunks=[feeds.RSS_BLOG])

    monkeypatch.setattr(ingest.requests, 'get', fake_get)
    ingest.fetch_feed(source)

    assert 'if-none-match' not in sent['headers']
    assert 'if-modified-since' not in sent['headers']


def test_a_youtube_entry_maps_its_thumbnail_and_published_date(db, monkeypatch):
    source = Source.objects.create(
        type=Source.Type.YOUTUBE, feed_url='https://youtube.com/feeds/videos.xml?channel_id=UCgij'
    )
    serve(monkeypatch, ok(feeds.ATOM_YOUTUBE))

    ingest_source(source)

    post = Post.objects.get()
    assert post.guid == 'yt:video:H14_F7bGgzg'
    assert post.image_url == 'https://i1.ytimg.com/vi/H14_F7bGgzg/hqdefault.jpg'
    assert post.summary == "The week's ski industry news"
    # published, not updated — YouTube bumps updated on view-count changes
    assert post.published_at.isoformat() == '2026-08-21T21:06:18+00:00'


def test_a_reddit_entry_maps_its_atom_id_as_the_guid(db, monkeypatch):
    source = Source.objects.create(
        type=Source.Type.REDDIT, feed_url='https://www.reddit.com/r/OnePiece/.rss'
    )
    serve(monkeypatch, ok(feeds.ATOM_REDDIT))

    ingest_source(source)

    post = Post.objects.get()
    assert post.guid == 'https://www.reddit.com/r/OnePiece/t3_1vw9fff'
    assert '<p>Chapter 1191 is out</p>' in post.summary


def test_an_image_enclosure_becomes_the_card_image(source, monkeypatch):
    serve(monkeypatch, ok(feeds.RSS_BLOG))

    ingest_source(source)

    assert Post.objects.get(guid='https://medium.com/p/two').image_url == (
        'https://cdn.example.com/two.jpg'
    )
    assert Post.objects.get(guid='https://medium.com/p/one').image_url == ''


def test_an_entry_without_a_link_is_skipped(source, monkeypatch):
    serve(monkeypatch, ok(feeds.RSS_NO_LINK))

    result = ingest_source(source)

    assert result.created == 1
    assert Post.objects.get().post_url == 'https://example.com/ok'


def test_an_entry_without_a_date_falls_back_to_now(source, monkeypatch):
    serve(monkeypatch, ok(feeds.RSS_NO_DATE))
    before = timezone.now()

    ingest_source(source)

    assert Post.objects.get().published_at >= before


def test_blank_source_metadata_is_backfilled_from_the_feed(source, monkeypatch):
    serve(monkeypatch, ok(feeds.RSS_BLOG))

    ingest_source(source)

    source.refresh_from_db()
    assert source.title == 'Vuejs on Medium'
    assert source.site_url == 'https://medium.com/tag/vuejs'
    # not the feed's RSS <image>, which is a logo — the site's favicon, guessed because the
    # test's site page is unreachable (conftest.no_icon_lookups)
    assert source.icon_url == 'https://medium.com/favicon.ico'


def test_a_feeds_own_atom_icon_is_kept_and_no_page_is_fetched(source, monkeypatch):
    """Atom's <icon> is square by definition — the one thing a feed says about its own
    picture that is safe to crop into a circle."""
    serve(monkeypatch, ok(feeds.ATOM_REDDIT))
    fetched = []
    monkeypatch.setattr(icons, 'fetch_page', fetched.append)

    ingest_source(source)

    source.refresh_from_db()
    assert source.icon_url == 'https://www.redditstatic.com/icon.png'
    assert fetched == []


def test_a_source_without_an_icon_gets_the_one_its_site_declares(source, monkeypatch):
    serve(monkeypatch, ok(feeds.RSS_BLOG))
    fetched = []

    def fetch_page(url):
        fetched.append(url)
        return b'<html><head><link rel="icon" href="/brand.svg" sizes="any"></head></html>'

    monkeypatch.setattr(icons, 'fetch_page', fetch_page)

    ingest_source(source)

    source.refresh_from_db()
    assert source.icon_url == 'https://medium.com/brand.svg'
    # the site the feed names, not the feed itself
    assert fetched == ['https://medium.com/tag/vuejs']


def test_a_youtube_source_gets_its_channels_avatar(source, monkeypatch):
    serve(monkeypatch, ok(feeds.ATOM_YOUTUBE))
    monkeypatch.setattr(
        icons,
        'fetch_page',
        lambda url: b'<meta property="og:image" content="https://yt3.googleusercontent.com/a">',
    )

    ingest_source(source)

    source.refresh_from_db()
    assert source.icon_url == 'https://yt3.googleusercontent.com/a'


def test_an_icon_is_looked_up_once_and_never_again(source, monkeypatch):
    """Whatever the first lookup stores — here the guess — ends the lookups for good."""
    serve(monkeypatch, ok(feeds.RSS_BLOG))
    ingest_source(source)

    fetched = []
    monkeypatch.setattr(icons, 'fetch_page', fetched.append)
    ingest_source(source)

    assert fetched == []


def test_backfill_truncates_to_each_columns_limit(source, monkeypatch):
    """Source.title is 300 chars and the URL columns are 500 — a feed can exceed either."""
    long_title = 'V' * 400
    serve(monkeypatch, ok(feeds.RSS_BLOG.replace(b'Vuejs on Medium', long_title.encode())))

    ingest_source(source)

    source.refresh_from_db()
    assert source.title == long_title[:300]


def test_backfill_never_overwrites_what_is_already_set(source, monkeypatch):
    source.title = 'My name for it'
    source.save(update_fields=['title'])
    serve(monkeypatch, ok(feeds.RSS_BLOG))

    ingest_source(source)

    source.refresh_from_db()
    assert source.title == 'My name for it'


def test_a_body_that_is_not_a_feed_is_an_error_not_a_crash(source, monkeypatch):
    serve(monkeypatch, ok(feeds.NOT_A_FEED))

    result = ingest_source(source)

    assert result.status == ERROR
    assert not Post.objects.exists()
    source.refresh_from_db()
    assert source.error_count == 1


def test_an_http_error_status_is_a_failure(source, monkeypatch):
    serve(monkeypatch, FetchResult(status_code=404))

    result = ingest_source(source)

    assert result.status == ERROR
    assert '404' in result.detail


def test_a_connection_failure_does_not_raise(source, monkeypatch):
    serve(monkeypatch, requests.ConnectionError('name or service not known'))

    result = ingest_source(source)

    assert result.status == ERROR
    source.refresh_from_db()
    assert source.error_count == 1


def test_the_backoff_grows_with_each_consecutive_failure(source, monkeypatch):
    serve(monkeypatch, FetchResult(status_code=500))

    ingest_source(source)
    source.refresh_from_db()
    first = source.next_fetch_at - timezone.now()

    ingest_source(source)
    source.refresh_from_db()
    second = source.next_fetch_at - timezone.now()

    assert first > POLL_INTERVAL
    assert second > first


def test_a_source_is_deactivated_after_repeated_failures(source, monkeypatch):
    serve(monkeypatch, FetchResult(status_code=500))

    for _ in range(MAX_FAILURES - 1):
        ingest_source(source)
    source.refresh_from_db()
    assert source.active is True

    ingest_source(source)

    source.refresh_from_db()
    assert source.active is False
    assert source.error_count == MAX_FAILURES


def test_a_crash_after_the_upsert_leaves_nothing_behind(source, monkeypatch):
    """The write phase is one transaction, so a worker killed mid-poll leaves no half-batch.

    Ingest is idempotent either way — the next poll would converge — but a partial write
    that outlives the process is exactly what T9's "no partial state" is about.
    """
    serve(monkeypatch, ok(feeds.RSS_BLOG))

    def killed(*args):
        raise RuntimeError('killed mid-poll')

    monkeypatch.setattr(ingest, '_backfill_source_metadata', killed)

    with pytest.raises(RuntimeError):
        ingest_source(source)

    assert not Post.objects.exists()
    source.refresh_from_db()
    assert source.last_fetched_at is None


def test_a_failure_leaves_last_fetched_at_alone(source, monkeypatch):
    """It means "when data last arrived" — a stale value beside a rising error count."""
    serve(monkeypatch, ok(feeds.RSS_BLOG), FetchResult(status_code=500))
    ingest_source(source)
    source.refresh_from_db()
    fetched_at = source.last_fetched_at

    ingest_source(source)

    source.refresh_from_db()
    assert source.last_fetched_at == fetched_at


def test_a_success_resets_the_error_count(source, monkeypatch):
    serve(monkeypatch, FetchResult(status_code=500), ok(feeds.RSS_BLOG))
    ingest_source(source)

    ingest_source(source)

    source.refresh_from_db()
    assert source.error_count == 0
    assert source.next_fetch_at < timezone.now() + POLL_INTERVAL * 1.2


def test_due_sources_skips_inactive_and_not_yet_due_sources(db):
    now = timezone.now()
    never_polled = Source.objects.create(type=Source.Type.WEBSITE, feed_url='https://a.example/rss')
    overdue = Source.objects.create(
        type=Source.Type.WEBSITE,
        feed_url='https://b.example/rss',
        next_fetch_at=now - timedelta(minutes=1),
    )
    Source.objects.create(
        type=Source.Type.WEBSITE,
        feed_url='https://c.example/rss',
        next_fetch_at=now + timedelta(hours=1),
    )
    Source.objects.create(type=Source.Type.WEBSITE, feed_url='https://d.example/rss', active=False)

    assert set(due_sources(now)) == {never_polled, overdue}


def test_poll_due_polls_only_what_is_due(db, monkeypatch):
    due = Source.objects.create(type=Source.Type.WEBSITE, feed_url='https://a.example/rss')
    Source.objects.create(
        type=Source.Type.WEBSITE,
        feed_url='https://c.example/rss',
        next_fetch_at=timezone.now() + timedelta(hours=1),
    )
    serve(monkeypatch, ok(feeds.RSS_BLOG))
    out = StringIO()

    call_command('poll_due', stdout=out)

    assert Post.objects.filter(source=due).count() == 2
    assert Post.objects.exclude(source=due).count() == 0
    assert '2 new post(s)' in out.getvalue()


def test_poll_due_says_so_when_nothing_is_due(db):
    Source.objects.create(
        type=Source.Type.WEBSITE,
        feed_url='https://c.example/rss',
        next_fetch_at=timezone.now() + timedelta(hours=1),
    )
    out = StringIO()

    call_command('poll_due', stdout=out)

    assert 'Nothing due.' in out.getvalue()


def test_poll_source_ignores_the_schedule(source, monkeypatch):
    source.next_fetch_at = timezone.now() + timedelta(hours=5)
    source.save(update_fields=['next_fetch_at'])
    serve(monkeypatch, ok(feeds.RSS_BLOG))
    out = StringIO()

    call_command('poll_source', source.uid, stdout=out)

    assert Post.objects.count() == 2
    assert '2 new' in out.getvalue()


def test_poll_source_rejects_an_unknown_uid(db):
    with pytest.raises(CommandError, match='No source with uid'):
        call_command('poll_source', 'source_nope')


# --- Content that must never crash the write phase -------------------------------------------
#
# The network phase never raises (tested above); the write phase must not either, or a
# source serving one unstorable entry fails on every poll without ever walking the backoff
# ladder: error_count never moves, so it is never deactivated, and the sweep re-enqueues it
# every half hour forever. Each test here is one thing a real feed can serve.


def test_nul_bytes_are_stripped_rather_than_crashing_the_write(source, monkeypatch):
    serve(monkeypatch, ok(feeds.RSS_NUL_BYTES))

    result = ingest_source(source)

    assert result.status == OK
    post = Post.objects.get()
    assert post.title == 'Bad title'
    assert post.summary == 'bad body'
    source.refresh_from_db()
    assert source.title == 'Nullish'


def test_an_oversized_summary_is_truncated(source, monkeypatch):
    """The search column is a tsvector, and Postgres caps one at 1 MB — a description the
    size of a book would fail the INSERT. Long before that it is not a summary."""
    huge = ' '.join(f'w{i}' for i in range(30_000))
    body = feeds.RSS_NO_DATE.replace(b'<link>', f'<description>{huge}</description><link>'.encode())
    serve(monkeypatch, ok(body))

    ingest_source(source)

    assert len(Post.objects.get().summary) == ingest.MAX_SUMMARY


def test_an_entry_whose_link_is_not_http_is_skipped(source, monkeypatch):
    serve(monkeypatch, ok(feeds.RSS_ODD_SCHEMES))

    result = ingest_source(source)

    assert result.created == 1
    assert Post.objects.get().post_url == 'https://example.com/fine'


def test_a_non_http_image_or_site_is_dropped_not_stored(source, monkeypatch):
    serve(monkeypatch, ok(feeds.RSS_ODD_SCHEMES))

    ingest_source(source)

    assert Post.objects.get().image_url == ''
    source.refresh_from_db()
    assert source.site_url == ''
    assert source.icon_url == ''
    assert source.title == 'Odd'


def test_a_future_published_date_is_clamped_to_now(source, monkeypatch):
    serve(monkeypatch, ok(feeds.RSS_FUTURE_DATE))
    before = timezone.now()

    ingest_source(source)

    assert before <= Post.objects.get().published_at <= timezone.now()


def test_a_write_the_database_refuses_is_a_recorded_failure_not_a_crash(source, monkeypatch):
    """Belt and braces under the sanitising above: whatever content-shaped rejection Postgres
    comes up with next walks the same backoff ladder as a dead feed, rather than looping."""
    from django.db import DataError

    serve(monkeypatch, ok(feeds.RSS_BLOG))

    def refused(*args):
        raise DataError('value too long for type character varying(5)')

    monkeypatch.setattr(ingest, '_upsert_posts', refused)

    result = ingest_source(source)

    assert result.status == ERROR
    assert 'value too long' in result.detail
    source.refresh_from_db()
    assert source.error_count == 1
    assert not Post.objects.exists()


# --- fetch_feed itself: the one function every other test here replaces -----------------------
#
# Polling shares core/fetch.py's address check and read cap with extraction and discovery,
# and these are the tests that it does — with requests.get replaced the way tests/test_fetch.py
# does it, and a literal public address so no resolver is involved.


def test_a_private_feed_url_is_a_failure_with_no_request_made(db, monkeypatch):
    source = Source.objects.create(type=Source.Type.WEBSITE, feed_url='http://127.0.0.1/rss')

    def explode(*args, **kwargs):
        raise AssertionError('should not have opened a socket')

    monkeypatch.setattr(ingest.requests, 'get', explode)

    result = ingest_source(source)

    assert result.status == ERROR
    assert 'non-public' in result.detail
    source.refresh_from_db()
    assert source.error_count == 1


def test_a_feed_past_the_size_cap_is_a_failure_not_a_download(db, monkeypatch):
    from tests.test_fetch import FakeResponse

    source = Source.objects.create(type=Source.Type.WEBSITE, feed_url='http://93.184.216.34/rss')
    too_big = FakeResponse(
        200, {'content-type': 'application/rss+xml'}, [b'x' * (ingest.MAX_FEED_BYTES + 1)]
    )
    monkeypatch.setattr(ingest.requests, 'get', lambda *args, **kwargs: too_big)

    result = ingest_source(source)

    assert result.status == ERROR
    assert 'larger than' in result.detail


def test_a_feed_within_the_cap_is_read_whole(db, monkeypatch):
    from tests.test_fetch import FakeResponse

    source = Source.objects.create(type=Source.Type.WEBSITE, feed_url='http://93.184.216.34/rss')
    response = FakeResponse(
        200, {'content-type': 'application/rss+xml', 'etag': '"v1"'}, [feeds.RSS_BLOG]
    )
    monkeypatch.setattr(ingest.requests, 'get', lambda *args, **kwargs: response)

    result = ingest_source(source)

    assert result.status == OK
    assert result.created == 2
    source.refresh_from_db()
    assert source.etag == '"v1"'
