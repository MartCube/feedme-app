"""GET /discover/posts — a candidate's newest posts, before it is added.

Every test replaces `discover.fetch_page`, as test_discover.py does, with the real bodies
from tests/feeds.py. The one exception is the private-address test, which needs the real
fetch to show the preview goes through core/fetch.py's guard.
"""

import pytest
import requests

from core import discover, ingest, youtube
from core.fetch import PageUnavailable
from core.ingest import FetchResult, ingest_source
from core.models import Post, Source
from tests import feeds as bodies

URL = 'https://medium.com/feed/tag/vuejs'
CHANNEL_FEED = 'https://www.youtube.com/feeds/videos.xml?channel_id=UCgijLHTEP5FLGY0V-vpNjXg'
VIDEOS_FEED = youtube.videos_feed(CHANNEL_FEED)

EMPTY_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Brand new</title></channel></rss>
"""


def serve(monkeypatch, pages):
    """Answer these URLs with these bodies; anything else 404s. Returns the URLs asked for."""
    requested = []

    def fetch_page(url):
        requested.append(url)
        body = pages.get(url)
        if body is None:
            raise PageUnavailable('HTTP 404')
        if isinstance(body, Exception):
            raise body
        return body

    monkeypatch.setattr(discover, 'fetch_page', fetch_page)
    return requested


def preview(client, feed_url=URL):
    return client.get('/api/v1/discover/posts', {'feed_url': feed_url})


def long_feed():
    """Twelve dated entries out of order, and one with no date in the middle."""
    days = [5, 12, 1, 9, 3, 11, 7, 2, 10, 4, 8, 6]
    items = [
        f'<item><title>Day {day}</title><link>https://example.com/{day}</link>'
        f'<pubDate>{day:02d} Aug 2026 09:00:00 GMT</pubDate></item>'
        for day in days
    ]
    items.insert(6, '<item><title>Undated</title><link>https://example.com/undated</link></item>')
    channel = f'<channel><title>Long</title>{"".join(items)}</channel>'
    return f'<?xml version="1.0"?><rss version="2.0">{channel}</rss>'.encode()


def test_preview_401s_without_a_token(client, monkeypatch):
    serve(monkeypatch, {URL: bodies.RSS_BLOG})
    assert preview(client).status_code == 401


def test_a_feed_previews_as_its_posts(authed_client, monkeypatch):
    serve(monkeypatch, {URL: bodies.RSS_BLOG})

    response = preview(authed_client)

    assert response.status_code == 200
    first, second = response.json()
    assert first['title'] == 'The Composition API'
    assert first['post_url'] == 'https://medium.com/p/one?source=rss'
    assert first['published_at'].startswith('2026-08-24T20:36:01')
    assert first['video'] is None
    assert second['title'] == 'Reactivity in depth'


def test_the_newest_ten_come_back_newest_first(authed_client, monkeypatch):
    serve(monkeypatch, {URL: long_feed()})

    titles = [post['title'] for post in preview(authed_client).json()]

    # the undated entry would be eleventh, so the cut takes it along with days 1 and 2
    assert titles == [f'Day {day}' for day in range(12, 2, -1)]


def test_an_undated_entry_has_no_date_and_sorts_last(authed_client, monkeypatch):
    # RSS_NO_DATE's entry, first in the document, after the blog's two dated ones in the answer
    undated = b'<item><title>Whenever</title><link>https://example.com/whenever</link></item>'
    body = bodies.RSS_BLOG.replace(b'<item>', undated + b'<item>', 1)
    serve(monkeypatch, {URL: body})

    posts = preview(authed_client).json()

    assert [post['title'] for post in posts] == [
        'The Composition API',
        'Reactivity in depth',
        'Whenever',
    ]
    assert posts[-1]['published_at'] is None


def test_the_preview_maps_exactly_what_subscribing_stores(db, monkeypatch):
    """The parity the reuse of ingest.entry_to_post exists for: same body, same posts."""
    serve(monkeypatch, {URL: bodies.RSS_BLOG})
    source = Source.objects.create(type=Source.Type.WEBSITE, feed_url=URL)
    monkeypatch.setattr(
        ingest,
        'fetch_feed',
        lambda source: FetchResult(
            status_code=200, body=bodies.RSS_BLOG, content_type='application/rss+xml'
        ),
    )
    ingest_source(source)

    fields = ['title', 'post_url', 'image_url', 'summary', 'published_at']
    stored = list(Post.objects.order_by('-published_at').values(*fields))
    previewed = [{name: post[name] for name in fields} for post in discover.preview_feed(URL)]

    assert previewed == stored


def test_entries_whose_link_is_not_http_are_left_out(authed_client, monkeypatch):
    serve(monkeypatch, {URL: bodies.RSS_ODD_SCHEMES})

    posts = preview(authed_client).json()

    assert [post['title'] for post in posts] == ['Fine']
    assert posts[0]['image'] is None


def test_a_youtube_candidate_previews_the_videos_only_feed(authed_client, monkeypatch):
    requested = serve(monkeypatch, {VIDEOS_FEED: bodies.ATOM_YOUTUBE_VIDEOS})

    posts = preview(authed_client, CHANNEL_FEED).json()

    assert requested == [VIDEOS_FEED]
    assert [post['title'] for post in posts] == ['Top 5 Fridays - Episode 268']
    assert posts[0]['video']['vertical'] is False


def test_a_channel_with_no_videos_feed_falls_back_and_still_skips_shorts(
    authed_client, monkeypatch
):
    requested = serve(monkeypatch, {CHANNEL_FEED: bodies.ATOM_YOUTUBE_WITH_SHORT})

    posts = preview(authed_client, CHANNEL_FEED).json()

    assert requested == [VIDEOS_FEED, CHANNEL_FEED]
    assert [post['title'] for post in posts] == ['Top 5 Fridays - Episode 268']


def test_a_video_gets_the_poster_subscribing_would_store(db, monkeypatch):
    serve(monkeypatch, {VIDEOS_FEED: bodies.ATOM_YOUTUBE})
    monkeypatch.setattr(youtube, 'has_hq720', lambda video_id: True)

    (post,) = discover.preview_feed(CHANNEL_FEED)

    assert post['image_url'] == 'https://i.ytimg.com/vi/H14_F7bGgzg/hq720.jpg'


def test_a_feed_with_nothing_in_it_is_an_empty_list(authed_client, monkeypatch):
    serve(monkeypatch, {URL: EMPTY_FEED})

    response = preview(authed_client)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    'outcome',
    [bodies.NOT_A_FEED, PageUnavailable('HTTP 503'), requests.ConnectionError('refused')],
    ids=['not-a-feed', 'unavailable', 'connection-error'],
)
def test_a_feed_that_cannot_be_read_is_a_422_not_an_empty_list(authed_client, monkeypatch, outcome):
    serve(monkeypatch, {URL: outcome})

    response = preview(authed_client)

    assert response.status_code == 422
    assert response.json()['detail'] == "Couldn't read that feed."


def test_a_missing_feed_url_is_ninjas_own_422(authed_client):
    assert authed_client.get('/api/v1/discover/posts').status_code == 422


def test_a_private_address_is_refused_by_the_fetch_guard(authed_client):
    # no stub: the real fetch_page, whose check_public refuses before any socket opens
    response = preview(authed_client, 'http://127.0.0.1/feed.xml')

    assert response.status_code == 422


def test_previewing_writes_nothing(authed_client, monkeypatch):
    serve(monkeypatch, {URL: long_feed()})
    before = (Source.objects.count(), Post.objects.count())

    assert preview(authed_client).status_code == 200

    assert (Source.objects.count(), Post.objects.count()) == before
