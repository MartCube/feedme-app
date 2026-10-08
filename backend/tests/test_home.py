"""GET /home — the cold-start round-trip — and PUT /home/order behind it."""

from typing import get_args

from django.db import connection
from django.test.utils import CaptureQueriesContext

from core import images
from core.api.home import FeedSourceSchema, SavedCountsSchema
from core.models import Feed, FeedSource, SavedPost, Source

EMPTY_COUNTS = {'bookmarks': 0, 'favorites': 0, 'later': 0}


def put_order(client, uids):
    return client.put('/api/v1/home/order', {'uids': uids}, content_type='application/json')


def query_count(client):
    with CaptureQueriesContext(connection) as queries:
        assert client.get('/api/v1/home').status_code == 200
    return len(queries)


def home_feeds(client):
    return client.get('/api/v1/home').json()['feeds']


def test_home_401s_without_a_token(client):
    assert client.get('/api/v1/home').status_code == 401


def test_reordering_401s_without_a_token(client):
    assert put_order(client, []).status_code == 401


def test_home_is_empty_for_a_fresh_account(authed_client):
    body = authed_client.get('/api/v1/home').json()

    assert body == {'feeds': [], 'saved_counts': EMPTY_COUNTS}


def test_a_feed_carries_its_name_description_and_sources(
    authed_client, user, make_feed, make_source
):
    source = make_source(
        type=Source.Type.YOUTUBE,
        feed_url='https://www.youtube.com/feeds/videos.xml?channel_id=abc',
        site_url='https://www.youtube.com/@fireship',
        icon_url='https://cdn.example.com/fireship.png',
        title='Fireship',
    )
    feed = make_feed(user, name='Videos', source=source)
    feed.description = 'Short ones.'
    feed.save()

    [body] = home_feeds(authed_client)

    assert body['name'] == 'Videos'
    assert body['description'] == 'Short ones.'
    assert body['sources'] == [
        {
            'uid': source.uid,
            'name': 'Fireship',
            'title': 'Fireship',
            'type': 'youtube',
            'site_url': 'https://www.youtube.com/@fireship',
            'feed_url': 'https://www.youtube.com/feeds/videos.xml?channel_id=abc',
            # through the proxy, never the stored URL itself (docs/images.md)
            'icon': images.icon('https://cdn.example.com/fireship.png'),
            'enabled': True,
        }
    ]


def test_a_renamed_source_shows_the_users_name_and_keeps_its_own_title(
    authed_client, user, make_feed, make_source
):
    source = make_source(title='Hacker News: Front Page')
    feed = make_feed(user, source=source)
    FeedSource.objects.filter(feed=feed).update(name='HN')

    [member] = home_feeds(authed_client)[0]['sources']

    assert member['name'] == 'HN'
    assert member['title'] == 'Hacker News: Front Page'


def test_sources_come_in_the_feeds_own_order_with_their_on_off(
    authed_client, user, make_feed, make_source
):
    a, b, c = make_source(title='A'), make_source(title='B'), make_source(title='C')
    make_feed(user, sources=[c, a, b], disabled=[a])

    sources = home_feeds(authed_client)[0]['sources']

    assert [s['name'] for s in sources] == ['C', 'A', 'B']  # FeedSource.order
    assert [s['enabled'] for s in sources] == [True, False, True]


def test_one_source_can_sit_in_two_feeds(authed_client, user, make_feed, make_source):
    shared = make_source(title='Shared')
    make_feed(user, name='One', source=shared)
    make_feed(user, name='Two', sources=[make_source(), shared], disabled=[shared], order=1)

    feeds = home_feeds(authed_client)

    assert [[s['enabled'] for s in f['sources'] if s['uid'] == shared.uid] for f in feeds] == [
        [True],
        [False],
    ]


def test_feeds_come_in_their_order(authed_client, user, make_feed):
    last = make_feed(user, name='Last', order=2)
    first = make_feed(user, name='First', order=0)

    assert [feed['uid'] for feed in home_feeds(authed_client)] == [first.uid, last.uid]


def test_a_feed_with_no_sources_is_still_listed(authed_client, user, make_feed):
    make_feed(user, name='Empty for now', sources=[])

    assert home_feeds(authed_client)[0]['sources'] == []


def test_saved_counts_are_reported_per_group(authed_client, user, make_post):
    for group, how_many in (('bookmarks', 2), ('later', 1)):
        for _ in range(how_many):
            SavedPost.objects.create(user=user, post=make_post(), group=group)

    counts = authed_client.get('/api/v1/home').json()['saved_counts']

    assert counts == {'bookmarks': 2, 'favorites': 0, 'later': 1}


def test_another_users_feeds_and_saves_never_appear(
    authed_client, user, other_user, make_feed, make_post
):
    mine = make_feed(user, name='Mine')
    make_feed(other_user, name='Theirs')
    SavedPost.objects.create(user=other_user, post=make_post(), group='bookmarks')

    body = authed_client.get('/api/v1/home').json()

    assert [feed['uid'] for feed in body['feeds']] == [mine.uid]
    assert body['saved_counts'] == EMPTY_COUNTS


def test_home_costs_the_same_number_of_queries_however_many_feeds_there_are(
    authed_client, user, make_feed, make_source
):
    make_feed(user, sources=[make_source() for _ in range(3)])
    small = query_count(authed_client)

    for n in range(5):
        make_feed(user, name=f'Big {n}', sources=[make_source() for _ in range(6)])
    large = query_count(authed_client)

    # 1 token lookup + feeds + their members with sources + saved counts. Pinned, not just
    # compared: this is the request every app launch waits on.
    assert small == large == 4


def test_the_order_survives_a_round_trip(authed_client, user, make_feed):
    a = make_feed(user, name='A', order=0)
    b = make_feed(user, name='B', order=1)
    c = make_feed(user, name='C', order=2)

    reordered = [b.uid, c.uid, a.uid]

    assert put_order(authed_client, reordered).status_code == 204
    assert [feed['uid'] for feed in home_feeds(authed_client)] == reordered


def test_reordering_rejects_a_uid_left_out_of_the_payload(authed_client, user, make_feed):
    kept = make_feed(user, name='Kept')
    forgotten = make_feed(user, name='Forgotten')

    response = put_order(authed_client, [kept.uid])

    assert response.status_code == 422
    assert forgotten.uid in response.json()['detail']


def test_reordering_rejects_a_uid_that_does_not_exist(authed_client, user, make_feed):
    feed = make_feed(user, name='Real')

    response = put_order(authed_client, [feed.uid, 'feed_madeup'])

    assert response.status_code == 422
    assert 'feed_madeup' in response.json()['detail']


def test_reordering_rejects_another_users_uid(authed_client, user, other_user, make_feed):
    mine = make_feed(user, name='Mine')
    theirs = make_feed(other_user, name='Theirs')

    response = put_order(authed_client, [mine.uid, theirs.uid])

    assert response.status_code == 422
    assert theirs.uid in response.json()['detail']


def test_reordering_rejects_a_repeated_uid(authed_client, user, make_feed):
    feed = make_feed(user, name='Only')

    response = put_order(authed_client, [feed.uid, feed.uid])

    assert response.status_code == 422
    assert 'duplicate' in response.json()['detail']


def test_a_rejected_reorder_writes_nothing(authed_client, user, make_feed):
    first = make_feed(user, name='First', order=0)
    second = make_feed(user, name='Second', order=1)

    assert put_order(authed_client, [second.uid]).status_code == 422

    assert Feed.objects.get(pk=first.pk).order == 0
    assert Feed.objects.get(pk=second.pk).order == 1


def test_the_source_types_literal_matches_the_models_choices():
    """Written out separately from Source.Type; this is what stops the two drifting."""
    annotation = FeedSourceSchema.model_fields['type'].annotation

    assert set(get_args(annotation)) == set(Source.Type.values)


def test_the_saved_count_keys_match_the_models_groups():
    """Same drift guard, on the other list written out by hand: a fourth saved group would
    otherwise be dropped from saved_counts without a single test noticing."""
    assert set(SavedCountsSchema.model_fields) == set(SavedPost.Group.values)
