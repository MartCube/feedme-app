"""The YouTube card's keyword search — GET /discover?type=youtube&q=<name>.

Every test replaces `youtube.fetch_search` and `youtube.fetch_statistics`, the module's two
network calls, the way
test_discover.py replaces `discover.fetch_page`. The canned body is a real `search.list`
answer trimmed to the fields we read, so what's parsed here is the shape Google sends.
"""

import pytest
import requests

from core import images, youtube

CHANNEL_ID = 'UCgijLHTEP5FLGY0V-vpNjXg'
VIDEOS = f'https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}'
THUMBNAIL = 'https://yt3.ggpht.com/ytc/AIdro_k=s88-c-k-c0x00ffffff-no-rj'

# search.list?part=snippet&type=channel — one channel hit, every field the API sends.
SEARCH_RESPONSE = {
    'kind': 'youtube#searchListResponse',
    'etag': 'abc',
    'regionCode': 'US',
    'pageInfo': {'totalResults': 1000000, 'resultsPerPage': 5},
    'items': [
        {
            'kind': 'youtube#searchResult',
            'etag': 'def',
            'id': {'kind': 'youtube#channel', 'channelId': CHANNEL_ID},
            'snippet': {
                'publishedAt': '2013-04-02T15:56:49Z',
                'channelId': CHANNEL_ID,
                'title': 'SkiEssentials',
                'description': 'Ski reviews and comparisons.',
                'thumbnails': {
                    'default': {'url': THUMBNAIL},
                    'medium': {'url': THUMBNAIL.replace('s88', 's240')},
                    'high': {'url': THUMBNAIL.replace('s88', 's800')},
                },
                'channelTitle': 'SkiEssentials',
                'liveBroadcastContent': 'none',
                'publishTime': '2013-04-02T15:56:49Z',
            },
        }
    ],
}


# channels.list?part=statistics for the hit above, trimmed to what we read.
STATISTICS_RESPONSE = {
    'kind': 'youtube#channelListResponse',
    'items': [
        {
            'kind': 'youtube#channel',
            'id': CHANNEL_ID,
            'statistics': {
                'viewCount': '98765432',
                'subscriberCount': '412000',
                'hiddenSubscriberCount': False,
                'videoCount': '1234',
            },
        }
    ],
}


@pytest.fixture(autouse=True)
def api_key(settings):
    settings.YOUTUBE_API_KEY = 'test-key'


def serve_statistics(monkeypatch, response=STATISTICS_RESPONSE):
    """Answer every statistics call with `response` (or raise it). Returns the ids asked."""
    asked = []

    def fetch_statistics(channel_ids):
        asked.append(list(channel_ids))
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(youtube, 'fetch_statistics', fetch_statistics)
    return asked


@pytest.fixture(autouse=True)
def statistics(monkeypatch):
    return serve_statistics(monkeypatch)


def serve(monkeypatch, response=SEARCH_RESPONSE):
    """Answer every search with `response` (or raise it). Returns the queries asked."""
    asked = []

    def fetch_search(query):
        asked.append(query)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(youtube, 'fetch_search', fetch_search)
    return asked


def search(client, q, type='youtube'):
    return client.get('/api/v1/discover', {'type': type, 'q': q})


def test_a_channel_name_finds_channels(authed_client, monkeypatch):
    serve(monkeypatch)

    body = search(authed_client, 'ski essentials').json()

    assert body == [
        {
            'name': 'SkiEssentials',
            'type': 'youtube',
            'site_url': f'https://www.youtube.com/channel/{CHANNEL_ID}',
            # the same videos.xml a pasted channel URL resolves to, so subscribing is the
            # same POST /feeds either way
            'feed_url': VIDEOS,
            'icon': images.icon(THUMBNAIL),
            'subscribers': 412000,
            'already_subscribed': False,
        }
    ]


def test_one_statistics_call_covers_every_hit(authed_client, monkeypatch, statistics):
    serve(monkeypatch)

    search(authed_client, 'ski essentials')
    search(authed_client, 'ski essentials')

    # one call for all the hits, and the cached search spends none
    assert statistics == [[CHANNEL_ID]]


def test_a_hidden_subscriber_count_is_null(authed_client, monkeypatch):
    serve(monkeypatch)
    hidden = {'items': [{'id': CHANNEL_ID, 'statistics': {'hiddenSubscriberCount': True}}]}
    serve_statistics(monkeypatch, hidden)

    assert search(authed_client, 'ski essentials').json()[0]['subscribers'] is None


def test_failed_statistics_still_answer_and_are_not_cached(authed_client, monkeypatch):
    asked = serve(monkeypatch)
    serve_statistics(monkeypatch, requests.ConnectionError())

    response = search(authed_client, 'ski essentials')

    # the hits are still worth showing; only the count is missing
    assert response.status_code == 200
    assert response.json()[0]['subscribers'] is None

    serve_statistics(monkeypatch)
    assert search(authed_client, 'ski essentials').json()[0]['subscribers'] == 412000
    # not cached without its counts, so the second search asked again
    assert len(asked) == 2


def test_a_keyword_under_another_card_never_asks_youtube(authed_client, monkeypatch):
    # the card says what a bare name means; 'ski essentials' under Website is nothing
    asked = serve(monkeypatch)

    assert search(authed_client, 'ski essentials', type='website').json() == []
    assert asked == []


def test_without_an_api_key_a_keyword_finds_nothing(authed_client, monkeypatch, settings):
    # degrades to T11a — URL and @handle still resolve, a name simply finds nothing
    settings.YOUTUBE_API_KEY = ''
    asked = serve(monkeypatch)

    response = search(authed_client, 'ski essentials')

    assert response.status_code == 200
    assert response.json() == []
    assert asked == []


def test_a_repeated_search_spends_no_quota(authed_client, monkeypatch):
    # search.list costs 100 of the day's 10k units; the second ask is answered from cache
    asked = serve(monkeypatch)

    first = search(authed_client, 'ski essentials').json()
    second = search(authed_client, 'ski essentials').json()

    assert first == second
    assert asked == ['ski essentials']


def test_the_cache_ignores_case_and_spacing(authed_client, monkeypatch):
    asked = serve(monkeypatch)

    search(authed_client, 'Ski Essentials')
    search(authed_client, '  ski   essentials ')

    assert len(asked) == 1


def test_a_handle_still_takes_the_free_path(authed_client, monkeypatch):
    # @handle resolved through the channel page before there was a key, and still does:
    # it costs no quota and needs no key
    asked = serve(monkeypatch)
    monkeypatch.setattr('core.discover.fetch_page', lambda url: b'<html></html>')

    search(authed_client, '@SkiEssentials')

    assert asked == []


@pytest.mark.parametrize(
    'failure',
    [requests.ConnectionError('refused'), requests.HTTPError('403 quotaExceeded')],
    ids=['network', 'quota'],
)
def test_youtube_being_down_is_a_503_not_an_empty_list(authed_client, monkeypatch, failure):
    # "Nothing found" for a blown quota would be a lie, and one that is hard to debug later
    serve(monkeypatch, failure)

    response = search(authed_client, 'ski essentials')

    assert response.status_code == 503
    assert response.json() == {'detail': 'YouTube search is unavailable right now.'}


def test_a_failed_search_is_not_cached(authed_client, monkeypatch):
    serve(monkeypatch, requests.ConnectionError('refused'))
    search(authed_client, 'ski essentials')

    asked = serve(monkeypatch)
    body = search(authed_client, 'ski essentials').json()

    # the retry went to the network, not to a cached failure
    assert asked == ['ski essentials']
    assert [result['name'] for result in body] == ['SkiEssentials']


def test_a_channel_you_follow_is_marked(authed_client, user, make_source, make_feed, monkeypatch):
    serve(monkeypatch)
    make_feed(user, source=make_source(feed_url=VIDEOS))

    assert search(authed_client, 'ski essentials').json()[0]['already_subscribed'] is True


def test_the_list_is_capped_even_when_youtube_overshoots(authed_client, monkeypatch):
    # seen live: maxResults=5 answered with resultsPerPage=6 for a channel search
    item = SEARCH_RESPONSE['items'][0]
    items = [
        {**item, 'id': {**item['id'], 'channelId': f'UC{n:022d}'}}
        for n in range(youtube.MAX_RESULTS + 1)
    ]
    serve(monkeypatch, {**SEARCH_RESPONSE, 'items': items})

    body = search(authed_client, 'one piece').json()

    assert len(body) == youtube.MAX_RESULTS


def test_a_search_with_no_hits_is_an_empty_list(authed_client, monkeypatch):
    serve(monkeypatch, {**SEARCH_RESPONSE, 'items': []})

    response = search(authed_client, 'xqzv nothing')

    assert response.status_code == 200
    assert response.json() == []


# --- posts: the poster and the player -------------------------------------------------------


def test_a_video_with_an_hq720_poster_gets_it(monkeypatch):
    monkeypatch.setattr(youtube, 'has_hq720', lambda video_id: True)

    assert youtube.poster('https://i1.ytimg.com/vi/H14_F7bGgzg/hqdefault.jpg') == (
        'https://i.ytimg.com/vi/H14_F7bGgzg/hq720.jpg'
    )


def test_a_video_without_one_keeps_hqdefault():
    # the conftest stub answers "no hq720"
    url = 'https://i1.ytimg.com/vi/H14_F7bGgzg/hqdefault.jpg'

    assert youtube.poster(url) == url


def test_the_poster_lookup_is_made_once_per_video(monkeypatch):
    calls = []
    monkeypatch.setattr(youtube, 'has_hq720', lambda video_id: calls.append(video_id) or True)

    youtube.poster('https://i1.ytimg.com/vi/H14_F7bGgzg/hqdefault.jpg')
    youtube.poster('https://i4.ytimg.com/vi/H14_F7bGgzg/hqdefault.jpg')

    assert calls == ['H14_F7bGgzg']


def test_a_failed_poster_lookup_is_not_remembered(monkeypatch):
    def down(video_id):
        raise requests.ConnectionError

    monkeypatch.setattr(youtube, 'has_hq720', down)
    url = 'https://i1.ytimg.com/vi/H14_F7bGgzg/hqdefault.jpg'
    assert youtube.poster(url) == url

    monkeypatch.setattr(youtube, 'has_hq720', lambda video_id: True)
    assert youtube.poster(url).endswith('/hq720.jpg')


def test_a_non_youtube_image_is_left_alone(monkeypatch):
    monkeypatch.setattr(youtube, 'has_hq720', lambda video_id: pytest.fail('looked up'))

    assert youtube.poster('https://i.redd.it/abc.jpeg') == 'https://i.redd.it/abc.jpeg'


def test_a_watch_link_plays_as_a_landscape_video():
    assert youtube.video('https://www.youtube.com/watch?v=v9QtM6qnG50') == {
        'src': 'https://www.youtube-nocookie.com/embed/v9QtM6qnG50?playsinline=1&rel=0',
        'vertical': False,
    }


def test_a_shorts_link_plays_as_a_vertical_video():
    assert youtube.video('https://www.youtube.com/shorts/CEJXqm2eiJ0') == {
        'src': 'https://www.youtube-nocookie.com/embed/CEJXqm2eiJ0?playsinline=1&rel=0',
        'vertical': True,
    }


@pytest.mark.parametrize(
    'post_url',
    [
        'https://www.reddit.com/r/OnePiece/comments/1vw9fff/chapter/',
        'https://www.youtube.com/channel/UCX6OQ3DkcsbYNE6H8uQQuVA',
        'https://evil.example/https://www.youtube.com/watch?v=v9QtM6qnG50',
        '',
    ],
)
def test_anything_else_has_no_player(post_url):
    assert youtube.video(post_url) is None
