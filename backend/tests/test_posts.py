"""The polymorphic post list, post detail, and the save toggle.

The list is one operation over five kinds of uid, so most of what's worth testing is that
each branch resolves to the right set — and that the cursor holds while the feed underneath
it keeps growing, which is the whole reason it isn't an offset.
"""

from datetime import timedelta
from typing import get_args

from django.db import connection
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from core.api.posts import SavedGroup
from core.auth import issue_token
from core.models import FeedSource, SavedPost

DAY = timedelta(days=1)
IMAGE = 'https://example.com/photo.jpg'

# the image tests care that the attributes arrive, not what they say — core/images.py's own
# tests pin the recipe. A fixed key keeps a signature stable, a fake base makes it obvious.
proxy_on = override_settings(
    IMGPROXY_KEY='aa' * 32, IMGPROXY_SALT='bb' * 32, IMGPROXY_PUBLIC_URL='http://img.test'
)


def get_posts(client, uid, **params):
    return client.get(f'/api/v1/feeds/{uid}/posts', params)


def save_request(client, post_uid, group='bookmarks'):
    return client.put(
        f'/api/v1/posts/{post_uid}/save', {'group': group}, content_type='application/json'
    )


def listed(response):
    return [post['uid'] for post in response.json()['items']]


def save(user, post, group='bookmarks', saved_at=None):
    """auto_now_add ignores a value handed to create(), so an explicit saved_at is an update."""
    saved = SavedPost.objects.create(user=user, post=post, group=group)
    if saved_at is not None:
        SavedPost.objects.filter(pk=saved.pk).update(saved_at=saved_at)
        saved.refresh_from_db()
    return saved


def test_the_post_list_401s_without_a_token(client):
    assert client.get('/api/v1/feeds/all/posts').status_code == 401


# --- which posts a uid means ----------------------------------------------------------


def test_all_merges_every_subscribed_feed_newest_first(authed_client, user, make_feed, make_post):
    now = timezone.now()
    vue, one_piece = make_feed(user, name='Vue'), make_feed(user, name='One Piece')
    older = make_post(source=vue.source, published_at=now - 2 * DAY)
    newest = make_post(source=one_piece.source, published_at=now)
    middle = make_post(source=vue.source, published_at=now - DAY)

    assert listed(get_posts(authed_client, 'all')) == [newest.uid, middle.uid, older.uid]


def test_all_excludes_a_source_the_user_does_not_subscribe_to(
    authed_client, user, make_feed, make_post, make_source
):
    mine = make_post(source=make_feed(user).source)
    make_post(source=make_source())  # global, but nobody here follows it

    assert listed(get_posts(authed_client, 'all')) == [mine.uid]


def test_a_feed_page_returns_only_that_feeds_posts(authed_client, user, make_feed, make_post):
    vue, one_piece = make_feed(user, name='Vue'), make_feed(user, name='One Piece')
    theirs = make_post(source=vue.source)
    make_post(source=one_piece.source)

    assert listed(get_posts(authed_client, vue.uid)) == [theirs.uid]


def test_a_feed_merges_its_sources_and_drops_the_switched_off_one(
    authed_client, user, make_feed, make_source, make_post
):
    now = timezone.now()
    heard, off, outside = make_source(), make_source(), make_source()
    feed = make_feed(user, name='Frontend', sources=[heard, off], disabled=[off])
    make_feed(user, name='Elsewhere', source=outside)
    wanted = make_post(source=heard, published_at=now)
    make_post(source=off, published_at=now - DAY)
    make_post(source=outside, published_at=now - 2 * DAY)

    assert listed(get_posts(authed_client, feed.uid)) == [wanted.uid]


def test_a_source_switched_off_in_one_feed_still_reads_in_another(
    authed_client, user, make_feed, make_source, make_post
):
    shared = make_source()
    make_feed(user, name='Off here', source=shared, disabled=[shared])
    on = make_feed(user, name='On here', source=shared)
    post = make_post(source=shared)

    assert listed(get_posts(authed_client, on.uid)) == [post.uid]


def test_all_leaves_out_a_source_switched_off_everywhere(
    authed_client, user, make_feed, make_source, make_post
):
    on, off = make_source(), make_source()
    make_feed(user, sources=[on, off], disabled=[off])
    kept = make_post(source=on)
    hidden = make_post(source=off)

    assert listed(get_posts(authed_client, 'all')) == [kept.uid]
    # off is a reading choice, not an unfollow: the post still opens
    assert authed_client.get(f'/api/v1/posts/{hidden.uid}').status_code == 200


def test_saved_returns_every_group_newest_saved_first(authed_client, user, make_feed, make_post):
    now = timezone.now()
    feed = make_feed(user)
    first, second, third = (make_post(source=feed.source) for _ in range(3))
    save(user, first, 'bookmarks', saved_at=now - 2 * DAY)
    save(user, second, 'later', saved_at=now)
    save(user, third, 'favorites', saved_at=now - DAY)

    # newest *saved* first, not newest published — a post saved this morning leads the pile
    assert listed(get_posts(authed_client, 'saved')) == [second.uid, third.uid, first.uid]


def test_saved_ignores_publication_order(authed_client, user, make_feed, make_post):
    now = timezone.now()
    feed = make_feed(user)
    ancient = make_post(source=feed.source, published_at=now - 900 * DAY)
    fresh = make_post(source=feed.source, published_at=now)
    save(user, fresh, saved_at=now - DAY)
    save(user, ancient, saved_at=now)

    assert listed(get_posts(authed_client, 'saved')) == [ancient.uid, fresh.uid]


def test_a_saved_group_returns_only_its_own(authed_client, user, make_feed, make_post):
    feed = make_feed(user)
    bookmarked, for_later = make_post(source=feed.source), make_post(source=feed.source)
    save(user, bookmarked, 'bookmarks')
    save(user, for_later, 'later')

    assert listed(get_posts(authed_client, 'saved_bookmarks')) == [bookmarked.uid]
    assert listed(get_posts(authed_client, 'saved_later')) == [for_later.uid]
    assert listed(get_posts(authed_client, 'saved_favorites')) == []


def test_an_unknown_uid_is_a_404(authed_client, user, make_feed):
    make_feed(user)

    for uid in ('nonsense', 'saved_starred', 'folder_madeup', 'feed_madeup'):
        assert get_posts(authed_client, uid).status_code == 404, uid


def test_another_users_feed_uid_is_a_404(authed_client, other_user, make_feed):
    theirs = make_feed(other_user, name='Theirs')

    assert get_posts(authed_client, theirs.uid).status_code == 404


# --- the fields that depend on who is asking ------------------------------------------


def test_each_post_carries_its_source_named_the_callers_way(
    authed_client, user, other_user, make_feed, make_source, make_post
):
    """One global post, two followers: the source's uid, type and site are shared, the name
    is each caller's own rename — or the source's title for one who never renamed it."""
    source = make_source(title='Hacker News: Front Page', site_url='https://news.ycombinator.com')
    mine = make_feed(user, source=source)
    make_feed(other_user, source=source)
    FeedSource.objects.filter(feed=mine).update(name='HN')
    make_post(source=source)

    their_client = Client(headers={'authorization': f'Bearer {issue_token(other_user)}'})

    assert get_posts(authed_client, 'all').json()['items'][0]['source'] == {
        'uid': source.uid,
        'name': 'HN',
        'type': 'website',
        'site_url': 'https://news.ycombinator.com',
    }
    assert get_posts(their_client, 'all').json()['items'][0]['source']['name'] == (
        'Hacker News: Front Page'
    )


def test_a_saved_post_whose_source_left_every_feed_still_says_where_it_came_from(
    authed_client, user, make_feed, make_post
):
    feed = make_feed(user)
    post = make_post(source=feed.source)
    save(user, post)
    feed.delete()  # unfollowed, but the saved post is never taken away

    item = get_posts(authed_client, 'saved').json()['items'][0]

    assert item['uid'] == post.uid
    assert item['source']['name'] == feed.source.title


def test_saved_group_is_null_until_the_post_is_saved(authed_client, user, make_feed, make_post):
    feed = make_feed(user)
    post = make_post(source=feed.source)

    assert get_posts(authed_client, 'all').json()['items'][0]['saved_group'] is None

    save(user, post, 'favorites')

    assert get_posts(authed_client, 'all').json()['items'][0]['saved_group'] == 'favorites'


def test_a_post_carries_the_summary_not_the_article(authed_client, user, make_feed, make_post):
    feed = make_feed(user)
    make_post(
        source=feed.source, summary='<p>what RSS gave us</p>', article_html='<p>extracted</p>'
    )

    item = get_posts(authed_client, 'all').json()['items'][0]

    assert item['summary'] == '<p>what RSS gave us</p>'
    assert 'article_html' not in item and 'content' not in item


# --- the image ------------------------------------------------------------------------


@proxy_on
def test_a_post_carries_ready_img_attributes_rather_than_the_raw_url(
    authed_client, user, make_feed, make_post
):
    """docs/images.md § Wire contract: the app puts these in the tag, and can't build one
    itself — the URLs are signed, and a key on the client is a key in the bundle."""
    post = make_post(source=make_feed(user).source, image_url=IMAGE)

    body = authed_client.get(f'/api/v1/posts/{post.uid}').json()

    assert 'image_url' not in body
    assert body['image']['src'].startswith('http://img.test/')
    assert '480w' in body['image']['srcset']


@proxy_on
def test_a_post_with_no_image_says_null(authed_client, user, make_feed, make_post):
    post = make_post(source=make_feed(user).source)

    assert authed_client.get(f'/api/v1/posts/{post.uid}').json()['image'] is None


@proxy_on
def test_the_list_carries_the_image_too(authed_client, user, make_feed, make_post):
    """List, detail and search share PostSchema; this is the one that renders ten at a time."""
    make_post(source=make_feed(user).source, image_url=IMAGE)

    items = get_posts(authed_client, 'all').json()['items']

    assert items[0]['image']['src'].endswith('.webp')


# --- the cursor -----------------------------------------------------------------------


def test_paging_skips_nothing_and_repeats_nothing_when_a_newer_post_arrives(
    authed_client, user, make_feed, make_post
):
    """The reason the cursor isn't an offset: a feed reader gets new rows mid-scroll."""
    now = timezone.now()
    feed = make_feed(user)
    posts = [make_post(source=feed.source, published_at=now - n * DAY) for n in range(4)]

    first = get_posts(authed_client, 'all', limit=2)
    assert listed(first) == [posts[0].uid, posts[1].uid]

    make_post(source=feed.source, published_at=now + DAY)  # arrives between the two requests

    second = get_posts(authed_client, 'all', limit=2, cursor=first.json()['next_cursor'])

    assert listed(second) == [posts[2].uid, posts[3].uid]
    assert second.json()['next_cursor'] is None


def test_the_saved_cursor_pages_by_save_time(authed_client, user, make_feed, make_post):
    now = timezone.now()
    feed = make_feed(user)
    posts = [make_post(source=feed.source) for _ in range(3)]
    for n, post in enumerate(posts):
        save(user, post, saved_at=now - n * DAY)

    first = get_posts(authed_client, 'saved', limit=2)
    second = get_posts(authed_client, 'saved', limit=2, cursor=first.json()['next_cursor'])

    assert listed(first) + listed(second) == [post.uid for post in posts]


def test_a_page_that_ends_the_list_carries_no_cursor(authed_client, user, make_feed, make_post):
    feed = make_feed(user)
    make_post(source=feed.source)

    assert get_posts(authed_client, 'all', limit=10).json()['next_cursor'] is None


def test_a_malformed_cursor_is_a_422(authed_client, user, make_feed):
    make_feed(user)

    response = get_posts(authed_client, 'all', cursor='not-a-cursor')

    assert response.status_code == 422
    assert response.json() == {'detail': 'invalid cursor'}


def test_a_cursor_with_a_naive_timestamp_is_a_422(authed_client, user, make_feed):
    """Every cursor we mint carries an offset. One without is a hand-built one, and Django
    would otherwise compare it in the default timezone with a warning in the log."""
    import base64

    make_feed(user)
    naive = base64.urlsafe_b64encode(b'2026-01-01T00:00:00|post_x').decode().rstrip('=')

    response = get_posts(authed_client, 'all', cursor=naive)

    assert response.status_code == 422
    assert response.json() == {'detail': 'invalid cursor'}


def test_a_limit_outside_the_allowed_range_is_a_422(authed_client, user, make_feed):
    make_feed(user)

    assert get_posts(authed_client, 'all', limit=0).status_code == 422
    assert get_posts(authed_client, 'all', limit=101).status_code == 422


def test_the_post_list_costs_the_same_queries_however_big_the_page(
    authed_client, user, make_feed, make_post
):
    feed = make_feed(user)
    for _ in range(30):
        make_post(source=feed.source)

    def cost(limit):
        with CaptureQueriesContext(connection) as queries:
            assert get_posts(authed_client, 'all', limit=limit).status_code == 200
        return len(queries)

    # 1 token lookup + 1 for the page. The subscribed sources and the three per-caller
    # fields are all subqueries, so none of them costs a round trip of its own.
    assert cost(1) == cost(100) == 2


# --- detail and the save toggle -------------------------------------------------------


def test_post_detail_returns_the_post(authed_client, user, make_feed, make_post):
    feed = make_feed(user)
    post = make_post(source=feed.source, title='The Composition API')

    body = authed_client.get(f'/api/v1/posts/{post.uid}').json()

    assert body['uid'] == post.uid
    assert body['title'] == 'The Composition API'
    assert body['source']['uid'] == feed.source.uid


def test_a_post_you_neither_follow_nor_saved_is_a_404(authed_client, user, make_feed, make_post):
    make_feed(user)
    stranger = make_post()  # its own source, unsubscribed

    assert authed_client.get(f'/api/v1/posts/{stranger.uid}').status_code == 404
    assert save_request(authed_client, stranger.uid).status_code == 404
    assert authed_client.delete(f'/api/v1/posts/{stranger.uid}/save').status_code == 404


def test_a_saved_post_stays_readable_after_unsubscribing(authed_client, user, make_feed, make_post):
    feed = make_feed(user)
    post = make_post(source=feed.source)
    save(user, post)
    feed.delete()

    assert authed_client.get(f'/api/v1/posts/{post.uid}').status_code == 200


def test_saving_a_post_then_moving_it_keeps_one_row(authed_client, user, make_feed, make_post):
    feed = make_feed(user)
    post = make_post(source=feed.source)

    created = save_request(authed_client, post.uid, 'bookmarks')
    assert created.status_code == 200
    assert created.json()['group'] == 'bookmarks'

    moved = save_request(authed_client, post.uid, 'later')
    assert moved.json()['group'] == 'later'
    # saved_at means "when this entered your pile", so a move doesn't reset it
    assert moved.json()['saved_at'] == created.json()['saved_at']

    assert SavedPost.objects.filter(user=user, post=post).count() == 1
    assert listed(get_posts(authed_client, 'saved_later')) == [post.uid]


def test_unsaving_removes_it_and_is_idempotent(authed_client, user, make_feed, make_post):
    feed = make_feed(user)
    post = make_post(source=feed.source)
    save(user, post)

    assert authed_client.delete(f'/api/v1/posts/{post.uid}/save').status_code == 204
    assert not SavedPost.objects.filter(user=user, post=post).exists()
    # a double-tapped toggle is a no-op, not an error
    assert authed_client.delete(f'/api/v1/posts/{post.uid}/save').status_code == 204


def test_a_group_outside_the_allowed_set_is_rejected(authed_client, user, make_feed, make_post):
    feed = make_feed(user)
    post = make_post(source=feed.source)

    assert save_request(authed_client, post.uid, 'starred').status_code == 422
    assert not SavedPost.objects.filter(user=user).exists()


def test_saves_are_per_account(authed_client, user, other_user, make_feed, make_source, make_post):
    source = make_source()
    make_feed(user, source=source)
    make_feed(other_user, source=source)
    post = make_post(source=source)
    save(other_user, post, 'favorites')

    assert get_posts(authed_client, 'all').json()['items'][0]['saved_group'] is None
    assert listed(get_posts(authed_client, 'saved')) == []


def test_the_saved_group_literal_matches_the_models_choices():
    """Written out separately from SavedPost.Group; this is what stops the two drifting."""
    assert set(get_args(SavedGroup)) == set(SavedPost.Group.values)
