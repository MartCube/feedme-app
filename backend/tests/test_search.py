"""GET /search — scoped post search.

Two engines answer one endpoint: a generated tsvector for whole words and stems, a trigram
index on the title for the partial words FTS structurally can't reach. Most of what's worth
testing is that both halves are actually live, that scoping is the post list's scoping and
not a second implementation of it, and that a person typing punctuation into a search box
can't reach the tsquery parser.
"""

import pathlib
from datetime import timedelta

from django.db import connection
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from core.models import SavedPost

DAY = timedelta(days=1)


def search(client, q, scope='all', **params):
    return client.get('/api/v1/search', {'q': q, 'scope': scope, **params})


def found(response):
    return [post['title'] for post in response.json()['items']]


# --- the two match branches ------------------------------------------------------------


def test_matches_a_whole_word_in_the_title(authed_client, user, make_feed, make_post):
    feed = make_feed(user)
    make_post(feed.source, title='Building a router from scratch')
    make_post(feed.source, title='Notes on kittens')

    assert found(search(authed_client, 'router')) == ['Building a router from scratch']


def test_matches_a_stemmed_word(authed_client, user, make_feed, make_post):
    """`routers` finds `router` only if the english dictionary is actually applied."""
    feed = make_feed(user)
    make_post(feed.source, title='Building a router from scratch')

    assert found(search(authed_client, 'routers')) == ['Building a router from scratch']


def test_matches_a_word_only_in_the_summary(authed_client, user, make_feed, make_post):
    """Weight B still reaches the vector — the summary is searched, just ranked lower."""
    feed = make_feed(user)
    make_post(feed.source, title='An unrelated headline', summary='all about capybaras')

    assert found(search(authed_client, 'capybaras')) == ['An unrelated headline']


def test_matches_a_partial_word(authed_client, user, make_feed, make_post):
    """The trigram half. `rout` is not a lexeme in `router`, so only ILIKE can find it."""
    feed = make_feed(user)
    make_post(feed.source, title='Building a router from scratch')

    assert found(search(authed_client, 'rout')) == ['Building a router from scratch']


def test_full_text_alone_cannot_find_a_partial_word(user, make_feed, make_post):
    """Pins *why* the trigram index exists — without this, dropping it looks harmless.

    Talks to core.search's FTS branch directly: through the endpoint the ILIKE branch would
    answer, and the assertion would pass whether or not FTS was doing anything.
    """
    from django.contrib.postgres.search import SearchQuery

    from core.models import SEARCH_CONFIG, Post

    feed = make_feed(user)
    make_post(feed.source, title='Building a router from scratch')

    fts_only = Post.objects.filter(
        search=SearchQuery('rout', config=SEARCH_CONFIG, search_type='websearch')
    )
    assert not fts_only.exists()


def test_html_tags_in_a_summary_are_not_searchable(authed_client, user, make_feed, make_post):
    """Postgres's default parser discards `tag` tokens — which is why nothing strips HTML.

    Reddit wraps a whole <table> around every summary. If markup reached the vector, one
    query for `table` would return every Reddit post an account follows.
    """
    feed = make_feed(user)
    make_post(
        feed.source,
        title='A reddit thread',
        summary='<table><tr><td>the actual sentence</td></tr></table>',
    )

    assert found(search(authed_client, 'table')) == []
    assert found(search(authed_client, 'sentence')) == ['A reddit thread']


def test_summary_is_not_substring_matched(authed_client, user, make_feed, make_post):
    """Partial-word matching is title-only, deliberately. Pinned so a later `summary__icontains`
    has to be a decision rather than a drive-by."""
    feed = make_feed(user)
    make_post(feed.source, title='An unrelated headline', summary='all about capybaras')

    assert found(search(authed_client, 'capybar')) == []


# --- scoping ---------------------------------------------------------------------------


def test_scopes_to_one_feed(authed_client, user, make_feed, make_post):
    mine = make_feed(user, name='Mine')
    other = make_feed(user, name='Other')
    make_post(mine.source, title='router in mine')
    make_post(other.source, title='router in other')

    assert found(search(authed_client, 'rout', scope=mine.uid)) == ['router in mine']


def test_scopes_to_a_folder_and_skips_its_muted_members(
    authed_client, user, make_feed, make_folder, make_post
):
    """The roadmap's acceptance: mute is applied live, with no re-index anywhere."""
    loud = make_feed(user, name='Loud')
    quiet = make_feed(user, name='Quiet')
    folder = make_folder(user, feeds=[loud, quiet], muted=[quiet])
    make_post(loud.source, title='router, audible')
    make_post(quiet.source, title='router, muted')

    assert found(search(authed_client, 'rout', scope=folder.uid)) == ['router, audible']
    # and the muted feed is still complete on its own page — mute belongs to the folder
    assert found(search(authed_client, 'rout', scope=quiet.uid)) == ['router, muted']


def test_scopes_to_saved_and_to_one_saved_group(authed_client, user, make_feed, make_post):
    feed = make_feed(user)
    bookmarked = make_post(feed.source, title='router, bookmarked')
    later = make_post(feed.source, title='router, later')
    make_post(feed.source, title='router, unsaved')
    SavedPost.objects.create(user=user, post=bookmarked, group='bookmarks')
    SavedPost.objects.create(user=user, post=later, group='later')

    assert sorted(found(search(authed_client, 'rout', scope='saved'))) == [
        'router, bookmarked',
        'router, later',
    ]
    assert found(search(authed_client, 'rout', scope='saved_later')) == ['router, later']


def test_a_saved_scope_orders_by_saved_at_not_published_at(
    authed_client, user, make_feed, make_post
):
    """Searching inside `saved` reads like the saved list it was opened from."""
    feed = make_feed(user)
    now = timezone.now()
    old_post_saved_late = make_post(
        feed.source, title='router, published long ago', published_at=now - 10 * DAY
    )
    new_post_saved_early = make_post(feed.source, title='router, published today', published_at=now)
    for post, saved_at in ((new_post_saved_early, now - DAY), (old_post_saved_late, now)):
        saved = SavedPost.objects.create(user=user, post=post, group='bookmarks')
        SavedPost.objects.filter(pk=saved.pk).update(saved_at=saved_at)

    assert found(search(authed_client, 'rout', scope='saved')) == [
        'router, published long ago',
        'router, published today',
    ]


def test_unsubscribed_feeds_are_never_searched(authed_client, user, make_post, make_source):
    """`scope=all` is what you follow, not the whole global Post table."""
    make_post(make_source(), title='router, followed by nobody')

    assert found(search(authed_client, 'rout')) == []


def test_another_users_scope_is_a_404(authed_client, other_user, make_feed, make_folder):
    theirs = make_feed(other_user)
    their_folder = make_folder(other_user, feeds=[theirs])

    assert search(authed_client, 'rout', scope=theirs.uid).status_code == 404
    assert search(authed_client, 'rout', scope=their_folder.uid).status_code == 404


def test_an_unknown_scope_is_a_404(authed_client):
    assert search(authed_client, 'rout', scope='nonsense').status_code == 404
    assert search(authed_client, 'rout', scope='saved_nonsense').status_code == 404


def test_search_requires_a_token():
    assert search(Client(), 'rout').status_code == 401


# --- input a person actually types -------------------------------------------------------


def test_hostile_queries_answer_empty_rather_than_raising(
    authed_client, user, make_feed, make_post
):
    """`websearch` is the reason this passes: `plain` would raise a syntax error into a 500."""
    feed = make_feed(user)
    make_post(feed.source, title='Building a router from scratch')

    for hostile in ('"unclosed', 'a & | b', '!', ':*', '<->', "''''"):
        response = search(authed_client, hostile)
        assert response.status_code == 200, hostile


def test_a_like_wildcard_is_matched_literally(authed_client, user, make_feed, make_post):
    """`%` is escaped, so it can't turn the trigram branch into a match-everything query."""
    feed = make_feed(user)
    make_post(feed.source, title='Building a router from scratch')

    assert found(search(authed_client, '%')) == []


def test_a_blank_query_is_an_empty_page_not_an_error(authed_client, user, make_feed, make_post):
    feed = make_feed(user)
    make_post(feed.source, title='Building a router from scratch')

    for blank in ('', '   '):
        body = search(authed_client, blank).json()
        assert body == {'items': [], 'next_cursor': None}


def test_a_blank_query_still_validates_the_scope(authed_client):
    """Typing nothing doesn't make a wrong scope right."""
    assert search(authed_client, '', scope='nonsense').status_code == 404


# --- paging ------------------------------------------------------------------------------


def test_the_cursor_walks_every_match_exactly_once(authed_client, user, make_feed, make_post):
    feed = make_feed(user)
    now = timezone.now()
    for n in range(5):
        make_post(feed.source, title=f'router {n}', published_at=now - n * DAY)
    make_post(feed.source, title='not a match', published_at=now)

    seen, cursor = [], None
    while True:
        body = search(authed_client, 'rout', limit=2, cursor=cursor or '').json()
        seen += [post['title'] for post in body['items']]
        cursor = body['next_cursor']
        if cursor is None:
            break

    assert seen == [f'router {n}' for n in range(5)]


def test_a_bad_cursor_is_a_422(authed_client, user, make_feed):
    make_feed(user)
    assert search(authed_client, 'rout', cursor='not-a-cursor').status_code == 422


def test_results_carry_the_per_caller_fields(authed_client, user, make_feed, make_post):
    """Same shape as the post list, so a card renders without a second request."""
    feed = make_feed(user)
    post = make_post(feed.source, title='Building a router from scratch')
    SavedPost.objects.create(user=user, post=post, group='favorites')

    item = search(authed_client, 'rout').json()['items'][0]
    assert item['feed_uid'] == feed.uid
    assert item['saved_group'] == 'favorites'


@override_settings(
    IMGPROXY_KEY='aa' * 32, IMGPROXY_SALT='bb' * 32, IMGPROXY_PUBLIC_URL='http://img.test'
)
def test_a_result_carries_the_same_image_shape_as_a_list_row(
    authed_client, user, make_feed, make_post
):
    """One schema behind three endpoints — a result that rendered differently would be a
    second kind of post (docs/images.md § Wire contract)."""
    make_post(make_feed(user).source, title='Kittens', image_url='https://e.com/k.jpg')

    item = search(authed_client, 'kittens').json()['items'][0]

    assert item['image']['src'].endswith('.webp')
    assert 'image_url' not in item


def test_query_count_does_not_grow_with_page_size(authed_client, user, make_feed, make_post):
    """The discipline T5 set: the per-caller fields are subqueries, so paging stays flat."""
    feed = make_feed(user)
    for n in range(20):
        make_post(feed.source, title=f'router {n}')

    with CaptureQueriesContext(connection) as small:
        search(authed_client, 'rout', limit=1)
    with CaptureQueriesContext(connection) as large:
        search(authed_client, 'rout', limit=20)

    assert len(small) == len(large)


# --- containment -------------------------------------------------------------------------


def test_only_the_search_module_touches_the_tsvector():
    """docs/backend.md § Search promises swapping engines is a one-module change.

    That is only true while nothing else queries the column, so it is asserted rather than
    trusted. Two exemptions, both schema rather than query: models.py *declares* the
    generated column, and migrations/ is a frozen copy of that declaration.
    """
    core = pathlib.Path(__file__).resolve().parent.parent / 'core'
    exempt = {core / 'search.py', core / 'models.py'}

    offenders = sorted(
        str(path.relative_to(core))
        for path in core.rglob('*.py')
        if path not in exempt
        and path.parent.name != 'migrations'
        and 'django.contrib.postgres.search' in path.read_text()
    )
    assert offenders == []


def test_a_nul_byte_in_the_query_finds_nothing_rather_than_crashing(
    authed_client, user, make_feed, make_post
):
    """Postgres refuses a NUL in a text parameter as loudly as in a column. Search is not
    a write, so it is not worth a 422 — the byte is dropped and the rest is searched."""
    make_post(source=make_feed(user).source, title='Composition API')

    response = search(authed_client, 'Composi\x00tion')

    assert response.status_code == 200
    assert found(response) == ['Composition API']
