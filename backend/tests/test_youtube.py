"""The YouTube card's keyword search — GET /discover?type=youtube&q=<name>.

Every test replaces `youtube.fetch_search`, the module's one network call, the way
test_discover.py replaces `discover.fetch_page`. The canned body is a real `search.list`
answer trimmed to the fields we read, so what's parsed here is the shape Google sends.
"""

import pytest
import requests

from core import youtube

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


@pytest.fixture(autouse=True)
def api_key(settings):
    settings.YOUTUBE_API_KEY = 'test-key'


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
            'icon_url': THUMBNAIL,
            'already_subscribed': False,
        }
    ]


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
