"""The feed writes: create / edit / delete a feed, and add / edit / remove its sources.

The reads live in test_home.py and test_posts.py; these are the writes behind the add wizard
and the feed page. Every test replaces ingest's one network call the way test_ingest.py does,
so adding a source never leaves the process.
"""

import pytest

from core import ingest
from core.api.feeds import infer_type
from core.ingest import FetchResult
from core.models import Feed, FeedSource, Post, Source
from tests import feeds as bodies

MEDIUM = 'https://medium.com/feed/tag/vuejs'
OTHER = 'https://example.org/rss'


def serve(monkeypatch, body=bodies.RSS_BLOG):
    """Answer every fetch with one body — adding a source fetches at most once."""

    def fetch(source):
        return FetchResult(status_code=200, body=body, content_type='application/rss+xml')

    monkeypatch.setattr(ingest, 'fetch_feed', fetch)


def create(client, **body):
    return client.post('/api/v1/feeds', body, content_type='application/json')


def update(client, uid, **body):
    return client.patch(f'/api/v1/feeds/{uid}', body, content_type='application/json')


def add(client, uid, feed_url=MEDIUM):
    return client.post(
        f'/api/v1/feeds/{uid}/sources', {'feed_url': feed_url}, content_type='application/json'
    )


def update_source(client, uid, source_uid, **body):
    return client.patch(
        f'/api/v1/feeds/{uid}/sources/{source_uid}', body, content_type='application/json'
    )


def remove(client, uid, source_uid):
    return client.delete(f'/api/v1/feeds/{uid}/sources/{source_uid}')


def test_the_writes_401_without_a_token(client):
    assert create(client, name='Nope').status_code == 401
    assert update(client, 'feed_x', name='Nope').status_code == 401
    assert client.delete('/api/v1/feeds/feed_x').status_code == 401
    assert add(client, 'feed_x').status_code == 401
    assert update_source(client, 'feed_x', 'source_x', enabled=False).status_code == 401
    assert remove(client, 'feed_x', 'source_x').status_code == 401


# --- Creating a feed ------------------------------------------------------------------------------


def test_a_feed_can_start_empty(authed_client, user):
    response = create(authed_client, name='  Skiing  ', description=' Gear and slopes. ')

    assert response.status_code == 201
    body = response.json()
    feed = Feed.objects.get(user=user)
    assert body == {
        'uid': feed.uid,
        'name': 'Skiing',
        'description': 'Gear and slopes.',
        'sources': [],
    }


def test_an_empty_feed_needs_a_name(authed_client):
    assert create(authed_client).status_code == 422
    assert create(authed_client, name='   ').status_code == 422
    assert not Feed.objects.exists()


def test_a_new_feed_with_a_url_fetches_the_source_and_takes_its_name(
    authed_client, user, monkeypatch
):
    serve(monkeypatch)

    body = create(authed_client, feed_url=MEDIUM).json()

    # the feed's own title, backfilled by the fetch rather than taken from the request
    assert body['name'] == 'Vuejs on Medium'
    [source] = body['sources']
    assert source['feed_url'] == MEDIUM
    assert source['site_url'] == 'https://medium.com/tag/vuejs'
    assert source['enabled'] is True
    assert Post.objects.filter(source__feed_url=MEDIUM).count() == 2


def test_a_name_given_with_the_url_wins_over_the_sources_own(authed_client, monkeypatch):
    serve(monkeypatch)

    body = create(authed_client, name='Vue', feed_url=MEDIUM).json()

    assert body['name'] == 'Vue'
    # the source keeps its own title; only the feed was named
    assert body['sources'][0]['name'] == 'Vuejs on Medium'


def test_a_new_feed_takes_its_first_sources_description_as_text(authed_client, monkeypatch):
    described = bodies.RSS_BLOG.replace(
        b'<title>Vuejs on Medium</title>',
        b'<title>Vuejs on Medium</title>'
        b'<description><![CDATA[<p>The latest &amp; <b>best</b>\n stories</p>]]></description>',
        1,
    )
    serve(monkeypatch, described)

    # flattened at ingest: no tags, entities decoded, whitespace collapsed
    assert create(authed_client, feed_url=MEDIUM).json()['description'] == (
        'The latest & best stories'
    )
    # one the user wrote wins
    body = create(authed_client, name='Mine', description='My words', feed_url=OTHER).json()
    assert body['description'] == 'My words'


def test_a_url_that_isnt_a_feed_422s_and_leaves_nothing_behind(authed_client, monkeypatch):
    serve(monkeypatch, bodies.NOT_A_FEED)

    response = create(authed_client, feed_url=MEDIUM)

    assert response.status_code == 422
    assert response.json()['detail'] == "That URL isn't a feed."
    # the whole point: a typo must not leave a dead global row, nor an empty feed
    assert not Source.objects.exists()
    assert not Feed.objects.exists()


def test_something_that_isnt_a_url_is_rejected_before_any_fetch(authed_client, monkeypatch):
    def explode(source):
        raise AssertionError('should not have fetched')

    monkeypatch.setattr(ingest, 'fetch_feed', explode)

    assert create(authed_client, feed_url='not a url').status_code == 422


def test_a_new_feed_lands_at_the_end_of_the_list(authed_client, user, make_feed):
    make_feed(user, name='First', order=0)
    make_feed(user, name='Second', order=4)

    uid = create(authed_client, name='Third').json()['uid']

    assert Feed.objects.get(uid=uid).order == 5


# --- Editing and deleting a feed ------------------------------------------------------------------


def test_editing_a_feed_changes_only_what_was_sent(authed_client, user, make_feed):
    feed = make_feed(user, name='Old')
    feed.description = 'Kept'
    feed.save()

    body = update(authed_client, feed.uid, name='  New  ').json()

    assert (body['name'], body['description']) == ('New', 'Kept')
    body = update(authed_client, feed.uid, description='').json()
    assert (body['name'], body['description']) == ('New', '')


@pytest.mark.parametrize('name', ['   ', 'a\x00b'])
def test_a_blank_or_nul_name_422s(authed_client, user, make_feed, name):
    """Postgres refuses a NUL in any text column — without the check it is a 500."""
    feed = make_feed(user, name='Keep me')

    assert update(authed_client, feed.uid, name=name).status_code == 422

    feed.refresh_from_db()
    assert feed.name == 'Keep me'


def test_deleting_a_feed_removes_it_and_its_members(authed_client, user, make_feed):
    feed = make_feed(user)

    assert authed_client.delete(f'/api/v1/feeds/{feed.uid}').status_code == 204

    assert not Feed.objects.filter(uid=feed.uid).exists()
    assert not FeedSource.objects.exists()


def test_deleting_the_last_feed_with_a_source_deactivates_it(authed_client, user, make_feed):
    feed = make_feed(user)

    authed_client.delete(f'/api/v1/feeds/{feed.uid}')

    feed.source.refresh_from_db()
    # kept, not deleted: its posts and anyone's saves survive, and coming back is free
    assert not feed.source.active


def test_a_source_still_in_another_feed_stays_active(
    authed_client, user, other_user, make_feed, make_source
):
    mine, theirs = make_source(), make_source()
    feed = make_feed(user, sources=[mine, theirs])
    make_feed(user, name='Also mine', source=mine)
    make_feed(other_user, source=theirs)

    authed_client.delete(f'/api/v1/feeds/{feed.uid}')

    mine.refresh_from_db()
    theirs.refresh_from_db()
    assert mine.active
    assert theirs.active


def test_another_users_feed_is_invisible_to_every_write(authed_client, other_user, make_feed):
    feed = make_feed(other_user, name='Not yours')
    source_uid = feed.source.uid

    assert update(authed_client, feed.uid, name='Mine now').status_code == 404
    assert authed_client.delete(f'/api/v1/feeds/{feed.uid}').status_code == 404
    assert add(authed_client, feed.uid).status_code == 404
    assert update_source(authed_client, feed.uid, source_uid, enabled=False).status_code == 404
    assert remove(authed_client, feed.uid, source_uid).status_code == 404

    feed.refresh_from_db()
    assert feed.name == 'Not yours'
    assert FeedSource.objects.get(feed=feed).enabled


# --- Adding a source ------------------------------------------------------------------------------


def test_adding_a_source_appends_it_to_the_feed(authed_client, user, make_feed, monkeypatch):
    serve(monkeypatch)
    feed = make_feed(user)

    response = add(authed_client, feed.uid)

    assert response.status_code == 201
    assert [s['feed_url'] for s in response.json()['sources']] == [feed.source.feed_url, MEDIUM]


def test_one_source_can_join_several_feeds(authed_client, user, make_feed, monkeypatch):
    serve(monkeypatch)
    one = make_feed(user, name='One', sources=[])
    two = make_feed(user, name='Two', sources=[])

    assert add(authed_client, one.uid).status_code == 201
    assert add(authed_client, two.uid).status_code == 201

    assert Source.objects.count() == 1
    assert Source.objects.get().feeds.count() == 2


def test_the_same_source_twice_in_one_feed_422s(authed_client, user, make_feed, monkeypatch):
    serve(monkeypatch)
    feed = make_feed(user, sources=[])
    assert add(authed_client, feed.uid).status_code == 201

    response = add(authed_client, feed.uid)

    assert response.status_code == 422
    assert response.json()['detail'] == 'That source is already in this feed.'
    assert FeedSource.objects.count() == 1


def test_a_second_follower_reuses_the_source_without_refetching(
    authed_client, user, other_user, make_feed, monkeypatch
):
    serve(monkeypatch)
    source = Source.objects.create(type=Source.Type.WEBSITE, feed_url=MEDIUM, title='Vuejs')
    make_feed(other_user, source=source)
    fetched_at = source.last_fetched_at

    assert add(authed_client, make_feed(user, sources=[]).uid).status_code == 201

    source.refresh_from_db()
    assert Source.objects.count() == 1
    assert source.last_fetched_at == fetched_at


def test_adding_reactivates_a_source_nobody_followed(authed_client, user, make_feed, monkeypatch):
    serve(monkeypatch)
    Source.objects.create(
        type=Source.Type.WEBSITE, feed_url=MEDIUM, title='Vuejs', active=False, error_count=3
    )

    assert add(authed_client, make_feed(user, sources=[]).uid).status_code == 201

    source = Source.objects.get()
    assert source.active
    assert source.error_count == 0
    # cleared so poll_due picks it up on the next sweep rather than after the old backoff
    assert source.next_fetch_at is None


# --- Editing and removing a source ----------------------------------------------------------------


def test_a_source_can_be_renamed_and_the_rename_cleared(authed_client, user, make_feed):
    feed = make_feed(user)
    source_uid = feed.source.uid

    [member] = update_source(authed_client, feed.uid, source_uid, name=' HN ').json()['sources']
    assert member['name'] == 'HN'

    [member] = update_source(authed_client, feed.uid, source_uid, name='').json()['sources']
    # back to the source's own title
    assert member['name'] == feed.source.title


def test_a_source_can_be_switched_off_in_one_feed_only(authed_client, user, make_feed, make_source):
    shared = make_source()
    one = make_feed(user, name='One', source=shared)
    two = make_feed(user, name='Two', source=shared)

    body = update_source(authed_client, one.uid, shared.uid, enabled=False).json()

    assert body['sources'][0]['enabled'] is False
    assert FeedSource.objects.get(feed=two).enabled


def test_changing_a_sources_link_swaps_the_source_and_keeps_the_row(
    authed_client, user, make_feed, monkeypatch
):
    serve(monkeypatch)
    feed = make_feed(user)
    old = feed.source
    FeedSource.objects.filter(feed=feed).update(name='Mine', enabled=False)

    response = update_source(authed_client, feed.uid, old.uid, feed_url=MEDIUM)

    assert response.status_code == 200
    [member] = response.json()['sources']
    assert member['feed_url'] == MEDIUM
    # the rename and the on/off belong to the row, not the source
    assert (member['name'], member['enabled']) == ('Mine', False)
    old.refresh_from_db()
    # the shared Source's URL was never edited; the old one just lost its last follower
    assert old.feed_url != MEDIUM
    assert not old.active


def test_changing_a_link_to_a_source_already_in_the_feed_422s(
    authed_client, user, make_feed, make_source
):
    a, b = make_source(), make_source()
    feed = make_feed(user, sources=[a, b])

    response = update_source(authed_client, feed.uid, a.uid, feed_url=b.feed_url)

    assert response.status_code == 422
    assert list(feed.members.values_list('source', flat=True)) == [a.pk, b.pk]


def test_changing_a_link_to_something_that_isnt_a_feed_changes_nothing(
    authed_client, user, make_feed, monkeypatch
):
    serve(monkeypatch, bodies.NOT_A_FEED)
    feed = make_feed(user)

    assert update_source(authed_client, feed.uid, feed.source.uid, feed_url=MEDIUM).status_code == (
        422
    )
    assert FeedSource.objects.get(feed=feed).source == feed.source


def test_removing_a_source_leaves_the_feed(authed_client, user, make_feed):
    feed = make_feed(user)

    response = remove(authed_client, feed.uid, feed.source.uid)

    assert response.status_code == 200
    assert response.json()['sources'] == []
    assert Feed.objects.filter(pk=feed.pk).exists()
    feed.source.refresh_from_db()
    assert not feed.source.active


def test_a_source_not_in_the_feed_404s(authed_client, user, make_feed, make_source):
    feed = make_feed(user)
    stranger = make_source()

    assert update_source(authed_client, feed.uid, stranger.uid, enabled=False).status_code == 404
    assert remove(authed_client, feed.uid, stranger.uid).status_code == 404


# --- What adding a source must not leave behind ---------------------------------------------------


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


def test_a_new_source_is_not_due_for_the_sweep_while_its_first_fetch_runs(
    authed_client, monkeypatch
):
    """The row exists before the inline fetch does, and a Source with next_fetch_at=None is
    due *now* — so without a claim, a sweep that fires mid-fetch polls the same source a
    second time from the worker. The claim is the sweep's own, and ingest overwrites it."""
    from core.ingest import due_sources

    def fetch(source):
        assert not due_sources().filter(pk=source.pk).exists()
        return FetchResult(
            status_code=200, body=bodies.RSS_BLOG, content_type='application/rss+xml'
        )

    monkeypatch.setattr(ingest, 'fetch_feed', fetch)

    assert create(authed_client, feed_url=MEDIUM).status_code == 201


def test_an_ingest_that_raises_leaves_no_source_behind(authed_client, monkeypatch):
    """Not just an ERROR result: anything that escapes ingest_source. Otherwise the next
    attempt finds the row, skips the fetch, and follows something with no posts."""

    def fetch(source):
        raise RuntimeError('killed mid-fetch')

    monkeypatch.setattr(ingest, 'fetch_feed', fetch)

    with pytest.raises(RuntimeError):
        create(authed_client, feed_url=MEDIUM)

    assert not Source.objects.exists()
    assert not Feed.objects.exists()


def test_a_url_past_the_column_limit_is_a_422_not_a_truncated_fetch(authed_client, monkeypatch):
    def explode(source):
        raise AssertionError('should not have fetched')

    monkeypatch.setattr(ingest, 'fetch_feed', explode)

    response = create(authed_client, feed_url='https://example.com/' + 'a' * 500)

    assert response.status_code == 422
    assert 'feed_url' in response.json()['detail']
    assert not Source.objects.exists()
