"""POST /feeds, PATCH /feeds/{uid}, DELETE /feeds/{uid} — subscribe, rename, unsubscribe.

The reads live in test_posts.py; these are the writes behind the add wizard and the edit
drawer. Every test replaces ingest's one network call the way test_ingest.py does, so
subscribing never leaves the process.
"""

import pytest

from core import ingest
from core.api.feeds import infer_type
from core.ingest import FetchResult
from core.models import Feed, FolderMember, Post, Source
from tests import feeds as bodies

MEDIUM = 'https://medium.com/feed/tag/vuejs'


def serve(monkeypatch, body=bodies.RSS_BLOG):
    """Answer every fetch with one body — subscribing fetches at most once."""

    def fetch(source):
        return FetchResult(status_code=200, body=body, content_type='application/rss+xml')

    monkeypatch.setattr(ingest, 'fetch_feed', fetch)


def subscribe(client, feed_url=MEDIUM, **body):
    return client.post(
        '/api/v1/feeds', {'feed_url': feed_url, **body}, content_type='application/json'
    )


def rename(client, uid, name):
    return client.patch(f'/api/v1/feeds/{uid}', {'name': name}, content_type='application/json')


def test_the_writes_401_without_a_token(client, monkeypatch):
    serve(monkeypatch)
    assert subscribe(client).status_code == 401
    assert rename(client, 'feed_x', 'Nope').status_code == 401
    assert client.delete('/api/v1/feeds/feed_x').status_code == 401


def test_subscribing_creates_the_source_and_fetches_its_posts(authed_client, user, monkeypatch):
    serve(monkeypatch)

    body = subscribe(authed_client).json()

    feed = Feed.objects.get(user=user)
    assert body['uid'] == feed.uid
    assert body['feed_url'] == MEDIUM
    # the feed's own title, backfilled by the fetch rather than taken from the request
    assert body['name'] == 'Vuejs on Medium'
    assert body['site_url'] == 'https://medium.com/tag/vuejs'
    assert Post.objects.filter(source__feed_url=MEDIUM).count() == 2


def test_subscribing_puts_the_feed_in_a_folder_when_asked(
    authed_client, user, make_folder, monkeypatch
):
    serve(monkeypatch)
    folder = make_folder(user, name='Dev')

    uid = subscribe(authed_client, folder_uid=folder.uid).json()['uid']

    assert list(folder.members.values_list('feed__uid', flat=True)) == [uid]


def test_subscribing_to_an_unknown_folder_404s(authed_client, monkeypatch):
    serve(monkeypatch)

    response = subscribe(authed_client, folder_uid='folder_nope')

    assert response.status_code == 404
    assert not Feed.objects.exists()


def test_a_url_that_isnt_a_feed_422s_and_leaves_no_source(authed_client, monkeypatch):
    serve(monkeypatch, bodies.NOT_A_FEED)

    response = subscribe(authed_client)

    assert response.status_code == 422
    assert response.json()['detail'] == "That URL isn't a feed."
    # the whole point: a typo must not leave a dead global row behind for everyone
    assert not Source.objects.exists()
    assert not Feed.objects.exists()


def test_something_that_isnt_a_url_is_rejected_before_any_fetch(authed_client, monkeypatch):
    def explode(source):
        raise AssertionError('should not have fetched')

    monkeypatch.setattr(ingest, 'fetch_feed', explode)

    assert subscribe(authed_client, feed_url='not a url').status_code == 422


def test_the_second_subscriber_reuses_the_source_without_refetching(
    authed_client, other_user, monkeypatch
):
    serve(monkeypatch)
    source = Source.objects.create(type=Source.Type.WEBSITE, feed_url=MEDIUM, title='Vuejs')
    Feed.objects.create(user=other_user, source=source, name='Theirs')
    fetched_at = source.last_fetched_at

    assert subscribe(authed_client).status_code == 201

    source.refresh_from_db()
    assert Source.objects.count() == 1
    assert source.last_fetched_at == fetched_at
    assert source.feeds.count() == 2


def test_subscribing_twice_to_the_same_source_422s(authed_client, monkeypatch):
    serve(monkeypatch)
    assert subscribe(authed_client).status_code == 201

    response = subscribe(authed_client)

    assert response.status_code == 422
    assert Feed.objects.count() == 1


def test_resubscribing_reactivates_a_source_nobody_followed(authed_client, monkeypatch):
    serve(monkeypatch)
    Source.objects.create(
        type=Source.Type.WEBSITE, feed_url=MEDIUM, title='Vuejs', active=False, error_count=3
    )

    assert subscribe(authed_client).status_code == 201

    source = Source.objects.get()
    assert source.active
    assert source.error_count == 0
    # cleared so poll_due picks it up on the next sweep rather than after the old backoff
    assert source.next_fetch_at is None


def test_a_new_feed_lands_at_the_end_of_the_top_level_order(
    authed_client, user, make_feed, make_folder, monkeypatch
):
    serve(monkeypatch)
    make_feed(user, name='First', order=0)
    make_folder(user, name='A folder', order=1)

    uid = subscribe(authed_client).json()['uid']

    assert Feed.objects.get(uid=uid).order == 2


def test_renaming_changes_only_the_users_own_name_for_it(authed_client, user, make_feed):
    feed = make_feed(user, name='Vuejs on Medium')

    body = rename(authed_client, feed.uid, '  Vue stuff  ').json()

    feed.refresh_from_db()
    assert body['name'] == 'Vue stuff'
    assert feed.name == 'Vue stuff'
    # the shared Source is untouched — it is every other subscriber's feed too
    assert body['feed_url'] == feed.source.feed_url


def test_renaming_to_blank_422s(authed_client, user, make_feed):
    feed = make_feed(user, name='Keep me')

    assert rename(authed_client, feed.uid, '   ').status_code == 422

    feed.refresh_from_db()
    assert feed.name == 'Keep me'


def test_unsubscribing_removes_the_feed_and_its_memberships(
    authed_client, user, make_feed, make_folder
):
    feed = make_feed(user)
    folder = make_folder(user, feeds=[feed])

    assert authed_client.delete(f'/api/v1/feeds/{feed.uid}').status_code == 204

    assert not Feed.objects.filter(uid=feed.uid).exists()
    assert not FolderMember.objects.filter(folder=folder).exists()


def test_unsubscribing_the_last_follower_deactivates_the_source(authed_client, user, make_feed):
    feed = make_feed(user)

    authed_client.delete(f'/api/v1/feeds/{feed.uid}')

    source = Source.objects.get(pk=feed.source_id)
    # kept, not deleted: its posts and anyone's saves survive, and re-subscribing is free
    assert not source.active


def test_unsubscribing_leaves_a_source_someone_else_still_follows_active(
    authed_client, user, other_user, make_feed, make_source
):
    source = make_source()
    feed = make_feed(user, source=source)
    make_feed(other_user, source=source)

    authed_client.delete(f'/api/v1/feeds/{feed.uid}')

    source.refresh_from_db()
    assert source.active


def test_another_users_feed_is_invisible_to_both_writes(authed_client, other_user, make_feed):
    feed = make_feed(other_user, name='Not yours')

    assert rename(authed_client, feed.uid, 'Mine now').status_code == 404
    assert authed_client.delete(f'/api/v1/feeds/{feed.uid}').status_code == 404

    feed.refresh_from_db()
    assert feed.name == 'Not yours'


@pytest.mark.parametrize(
    ('url', 'expected'),
    [
        ('https://www.youtube.com/feeds/videos.xml?channel_id=abc', Source.Type.YOUTUBE),
        ('https://youtube.com/feeds/videos.xml', Source.Type.YOUTUBE),
        ('https://www.reddit.com/r/OnePiece/.rss', Source.Type.REDDIT),
        ('https://medium.com/feed/tag/vuejs', Source.Type.WEBSITE),
        # the host has to *end* with the domain, not merely contain it
        ('https://notyoutube.com/rss', Source.Type.WEBSITE),
    ],
)
def test_the_source_type_is_inferred_from_the_host(url, expected):
    assert infer_type(url) == expected
