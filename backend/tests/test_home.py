"""GET /home — the cold-start round-trip — and PUT /home/order behind it."""

from typing import get_args

from django.db import connection
from django.test.utils import CaptureQueriesContext

from core.api.home import HomeFeedSchema, SavedCountsSchema
from core.models import Feed, Folder, SavedPost, Source

EMPTY_COUNTS = {'bookmarks': 0, 'favorites': 0, 'later': 0}


def put_order(client, uids):
    return client.put('/api/v1/home/order', {'uids': uids}, content_type='application/json')


def query_count(client):
    with CaptureQueriesContext(connection) as queries:
        assert client.get('/api/v1/home').status_code == 200
    return len(queries)


def test_home_401s_without_a_token(client):
    assert client.get('/api/v1/home').status_code == 401


def test_reordering_401s_without_a_token(client):
    assert put_order(client, []).status_code == 401


def test_home_is_empty_for_a_fresh_account(authed_client):
    body = authed_client.get('/api/v1/home').json()

    assert body == {'folders': [], 'feeds': [], 'order': [], 'saved_counts': EMPTY_COUNTS}


def test_a_feed_carries_its_own_name_and_its_sources_metadata(
    authed_client, user, make_feed, make_source
):
    source = make_source(
        type=Source.Type.YOUTUBE,
        feed_url='https://www.youtube.com/feeds/videos.xml?channel_id=abc',
        site_url='https://www.youtube.com/@fireship',
        icon_url='https://cdn.example.com/fireship.png',
        title='Fireship',
    )
    make_feed(user, name='Fireship (renamed)', source=source)

    feed = authed_client.get('/api/v1/home').json()['feeds'][0]

    assert feed['name'] == 'Fireship (renamed)'  # the user's name, never the Source title
    assert feed['type'] == 'youtube'
    assert feed['site_url'] == 'https://www.youtube.com/@fireship'
    assert feed['icon_url'] == 'https://cdn.example.com/fireship.png'
    # Source is backend-only: its uid must not leak into the public contract
    assert 'source_uid' not in feed


def test_a_folder_lists_its_members_in_order_with_the_muted_subset(
    authed_client, user, make_feed, make_folder
):
    a, b, c = (make_feed(user, name=name) for name in ('A', 'B', 'C'))
    make_folder(user, name='Vue', feeds=[c, a, b], muted=[a])

    folder = authed_client.get('/api/v1/home').json()['folders'][0]

    assert folder['name'] == 'Vue'
    assert folder['feed_uids'] == [c.uid, a.uid, b.uid]  # FolderMember.order, not creation order
    assert folder['muted_feed_uids'] == [a.uid]


def test_feeds_carries_folder_members_as_well_as_loose_ones(
    authed_client, user, make_feed, make_folder
):
    inside = make_feed(user, name='Inside')
    loose = make_feed(user, name='Loose')
    make_folder(user, feeds=[inside])

    body = authed_client.get('/api/v1/home').json()

    assert {feed['uid'] for feed in body['feeds']} == {inside.uid, loose.uid}


def test_the_order_interleaves_folders_and_loose_feeds_and_omits_members(
    authed_client, user, make_feed, make_folder
):
    member = make_feed(user, name='Member')
    first = make_feed(user, name='First', order=1)
    last = make_feed(user, name='Last', order=3)
    folder = make_folder(user, name='Folder', feeds=[member], order=2)

    order = authed_client.get('/api/v1/home').json()['order']

    assert order == [first.uid, folder.uid, last.uid]
    # a member's position lives on FolderMember.order, so it is not a top-level entry
    assert member.uid not in order


def test_saved_counts_are_reported_per_group(authed_client, user, make_post):
    for group, how_many in (('bookmarks', 2), ('later', 1)):
        for _ in range(how_many):
            SavedPost.objects.create(user=user, post=make_post(), group=group)

    counts = authed_client.get('/api/v1/home').json()['saved_counts']

    assert counts == {'bookmarks': 2, 'favorites': 0, 'later': 1}


def test_another_users_feeds_folders_and_saves_never_appear(
    authed_client, user, other_user, make_feed, make_folder, make_post
):
    mine = make_feed(user, name='Mine')
    theirs = make_feed(other_user, name='Theirs')
    make_folder(other_user, name='Their folder', feeds=[theirs])
    SavedPost.objects.create(user=other_user, post=make_post(), group='bookmarks')

    body = authed_client.get('/api/v1/home').json()

    assert [feed['uid'] for feed in body['feeds']] == [mine.uid]
    assert body['folders'] == []
    assert body['order'] == [mine.uid]
    assert body['saved_counts'] == EMPTY_COUNTS


def test_home_costs_the_same_number_of_queries_however_many_feeds_there_are(
    authed_client, user, make_feed, make_folder
):
    make_folder(user, name='Small', feeds=[make_feed(user) for _ in range(3)])
    small = query_count(authed_client)

    for n in range(5):
        make_folder(user, name=f'Big {n}', feeds=[make_feed(user) for _ in range(6)])
    large = query_count(authed_client)

    # 1 token lookup + folders + their members + feeds + saved counts. Pinned, not just
    # compared: this is the request every app launch waits on.
    assert small == large == 5


def test_the_order_survives_a_round_trip(authed_client, user, make_feed, make_folder):
    a = make_feed(user, name='A')
    b = make_feed(user, name='B')
    folder = make_folder(user, name='Folder')

    reordered = [b.uid, folder.uid, a.uid]

    assert put_order(authed_client, reordered).status_code == 204
    assert authed_client.get('/api/v1/home').json()['order'] == reordered


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


def test_reordering_rejects_a_feed_that_lives_inside_a_folder(
    authed_client, user, make_feed, make_folder
):
    member = make_feed(user, name='Member')
    folder = make_folder(user, name='Folder', feeds=[member])

    response = put_order(authed_client, [folder.uid, member.uid])

    assert response.status_code == 422
    assert 'not a top-level uid' in response.json()['detail']


def test_reordering_rejects_a_repeated_uid(authed_client, user, make_feed):
    feed = make_feed(user, name='Only')

    response = put_order(authed_client, [feed.uid, feed.uid])

    assert response.status_code == 422
    assert 'duplicate' in response.json()['detail']


def test_a_rejected_reorder_writes_nothing(authed_client, user, make_feed, make_folder):
    feed = make_feed(user, name='Feed', order=0)
    folder = make_folder(user, name='Folder', order=1)

    assert put_order(authed_client, [folder.uid]).status_code == 422

    assert Feed.objects.get(pk=feed.pk).order == 0
    assert Folder.objects.get(pk=folder.pk).order == 1


def test_the_feed_types_literal_matches_the_models_choices():
    """Written out separately from Source.Type; this is what stops the two drifting."""
    annotation = HomeFeedSchema.model_fields['type'].annotation

    assert set(get_args(annotation)) == set(Source.Type.values)


def test_the_saved_count_keys_match_the_models_groups():
    """Same drift guard, on the other list written out by hand: a fourth saved group would
    otherwise be dropped from saved_counts without a single test noticing."""
    assert set(SavedCountsSchema.model_fields) == set(SavedPost.Group.values)
