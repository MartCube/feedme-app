"""GET /discover — what the add wizard's search step gets back.

Every test replaces `discover.fetch_page`, the module's one network call, the way
test_article.py replaces extract's — so resolving a URL never leaves the process. The feed
bodies are the real ones from tests/feeds.py; the HTML is here, since only this module
reads pages rather than feeds.
"""

import pytest

from core import discover, images
from core.fetch import PageUnavailable
from core.models import Feed
from tests import feeds as bodies

MEDIUM = 'https://medium.com/feed/tag/vuejs'
CHANNEL_ID = 'UCgijLHTEP5FLGY0V-vpNjXg'
VIDEOS = f'https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}'
ONEPIECE = 'https://www.reddit.com/r/OnePiece/.rss'

# A WordPress-shaped head: the posts feed and the comments feed, same rel and same type,
# one of them relative — which of the two you meant is the user's call, not ours.
HTML_WITH_FEEDS = b"""<!doctype html><html><head>
<title>CSS-Tricks</title>
<link rel="stylesheet" href="/style.css">
<link rel="alternate" type="application/rss+xml" title="CSS-Tricks &raquo; Feed" href="/feed/">
<link rel="alternate" type="application/rss+xml" title="CSS-Tricks &raquo; Comments Feed"
      href="https://css-tricks.com/comments/feed/">
</head><body><h1>Articles</h1></body></html>
"""

# A post page: what somebody actually has in the address bar when they decide to
# subscribe, and it declares no feed of its own. Nuxt's really does offer only markdown.
HTML_POST = b"""<!doctype html><html><head>
<title>Meet Nuxi &middot; Nuxt Blog</title>
<link rel="alternate" type="text/markdown" href="/blog/meet-nuxi.md">
</head><body><article>Nuxi is the new CLI.</article></body></html>
"""

# The section index above it, which does declare one.
HTML_SECTION = b"""<!doctype html><html><head>
<title>Nuxt Blog</title>
<link rel="alternate" type="application/atom+xml" title="Nuxt Blog RSS" href="/blog/rss.xml">
</head><body></body></html>
"""

# One feed, and a link tag whose title= is written for machines. The page knows better.
HTML_MACHINE_TITLE = b"""<!doctype html><html><head>
<title>CSS-Tricks</title>
<link rel="alternate" type="application/rss+xml" title="RSS 2.0" href="/feed/">
</head><body></body></html>
"""

# Declares nothing — the static-site-generator case the common-path guesses exist for.
HTML_BARE = b"""<!doctype html><html><head><title>Some Blog</title></head>
<body><p>Posts</p></body></html>
"""

# A channel page, trimmed to the tag that matters — but keeping the shape that broke:
# YouTube closes <head> after ~700 KB of inline script and then declares its title and its
# feed in the *body*. A parser that stops at </head> finds neither.
HTML_YOUTUBE = f"""<!doctype html><html><head><script>var ytcfg = 1;</script></head>
<body>
<title>SkiEssentials - YouTube</title>
<link rel="alternate" type="application/rss+xml" title="RSS" href="{VIDEOS}">
</body></html>
""".encode()


def serve(monkeypatch, pages):
    """Answer these URLs with these bodies; anything else 404s, as a real miss would.

    Returns the list of URLs asked for, in order — the cheap paths are only cheap if
    nothing else got fetched, and that is an assertion, not a comment.
    """
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


def search(client, q, type='website'):
    return client.get('/api/v1/discover', {'type': type, 'q': q})


def test_discover_401s_without_a_token(client, monkeypatch):
    serve(monkeypatch, {})
    assert search(client, MEDIUM).status_code == 401


def test_a_pasted_feed_url_comes_back_as_one_candidate(authed_client, monkeypatch):
    serve(monkeypatch, {MEDIUM: bodies.RSS_BLOG})

    body = search(authed_client, MEDIUM).json()

    assert body == [
        {
            # the feed's own title, not the hostname — the same read subscribing does
            'name': 'Vuejs on Medium',
            'type': 'website',
            'site_url': 'https://medium.com/tag/vuejs',
            'feed_url': MEDIUM,
            # the feed's RSS <image> is a logo, not an icon, and there's no page in hand to
            # read one from — so the free guess at the site's favicon (core/icons.py)
            'icon': images.icon('https://medium.com/favicon.ico'),
            # a count only a YouTube search hit carries
            'subscribers': None,
            'already_subscribed': False,
        }
    ]


def test_a_homepage_offers_every_feed_it_declares(authed_client, monkeypatch):
    serve(monkeypatch, {'https://css-tricks.com': HTML_WITH_FEEDS})

    body = search(authed_client, 'https://css-tricks.com').json()

    assert [(result['name'], result['feed_url']) for result in body] == [
        # relative href absolutised, entities in the title decoded
        ('CSS-Tricks » Feed', 'https://css-tricks.com/feed/'),
        ('CSS-Tricks » Comments Feed', 'https://css-tricks.com/comments/feed/'),
    ]


def test_declared_feeds_are_not_fetched_to_be_listed(authed_client, monkeypatch):
    # subscribing fetches for real and takes the true title from the feed, so confirming
    # each candidate here would triple the wait to improve a label
    requested = serve(monkeypatch, {'https://css-tricks.com': HTML_WITH_FEEDS})

    search(authed_client, 'https://css-tricks.com')

    assert requested == ['https://css-tricks.com']


def test_candidates_from_a_page_carry_the_icon_that_page_declares(authed_client, monkeypatch):
    """Read off the page discovery already fetched for its feed links — no extra request."""
    page = HTML_WITH_FEEDS.replace(
        b'<title>', b'<link rel="apple-touch-icon" href="/touch.png"><title>'
    )
    requested = serve(monkeypatch, {'https://css-tricks.com': page})

    body = search(authed_client, 'https://css-tricks.com').json()

    assert {result['icon'] for result in body} == {images.icon('https://css-tricks.com/touch.png')}
    assert requested == ['https://css-tricks.com']


def test_a_page_that_declares_no_icon_gets_the_favicon_guess(authed_client, monkeypatch):
    serve(monkeypatch, {'https://css-tricks.com': HTML_WITH_FEEDS})

    body = search(authed_client, 'https://css-tricks.com').json()

    assert body[0]['icon'] == images.icon('https://css-tricks.com/favicon.ico')


def test_a_page_declaring_nothing_falls_back_to_the_common_paths(authed_client, monkeypatch):
    requested = serve(
        monkeypatch,
        {'https://someblog.com': HTML_BARE, 'https://someblog.com/atom.xml': bodies.RSS_BLOG},
    )

    body = search(authed_client, 'https://someblog.com').json()

    assert [result['feed_url'] for result in body] == ['https://someblog.com/atom.xml']
    # in order, and it stops at the first hit rather than collecting them all
    assert requested == [
        'https://someblog.com',
        'https://someblog.com/feed',
        'https://someblog.com/rss',
        'https://someblog.com/rss.xml',
        'https://someblog.com/atom.xml',
    ]


def test_a_page_serving_html_at_a_guessed_path_is_not_a_feed(authed_client, monkeypatch):
    # a site that answers /feed with its 404 page rather than a 404 status
    serve(
        monkeypatch,
        {'https://someblog.com': HTML_BARE, 'https://someblog.com/feed': bodies.NOT_A_FEED},
    )

    assert search(authed_client, 'https://someblog.com').json() == []


def test_a_site_with_no_feed_anywhere_finds_nothing(authed_client, monkeypatch):
    serve(monkeypatch, {'https://someblog.com': HTML_BARE})

    response = search(authed_client, 'https://someblog.com')

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    'query', ['OnePiece', 'r/OnePiece', '/r/OnePiece', 'https://www.reddit.com/r/OnePiece/']
)
def test_a_subreddit_resolves_by_name_or_url(authed_client, monkeypatch, query):
    requested = serve(monkeypatch, {ONEPIECE: bodies.ATOM_REDDIT})

    body = search(authed_client, query, type='reddit').json()

    assert [(result['name'], result['type'], result['feed_url']) for result in body] == [
        ('One Piece', 'reddit', ONEPIECE)
    ]
    # straight to the .rss — fetching the subreddit's HTML page first would buy nothing
    assert requested == [ONEPIECE]


def test_a_subreddit_that_does_not_exist_finds_nothing(authed_client, monkeypatch):
    serve(monkeypatch, {})

    assert search(authed_client, 'NotARealSubreddit', type='reddit').json() == []


def test_a_youtube_channel_url_resolves_without_fetching_the_page(authed_client, monkeypatch):
    requested = serve(monkeypatch, {VIDEOS: bodies.ATOM_YOUTUBE})

    body = search(
        authed_client, f'https://www.youtube.com/channel/{CHANNEL_ID}', type='youtube'
    ).json()

    assert [(result['name'], result['type'], result['feed_url']) for result in body] == [
        ('SkiEssentials', 'youtube', VIDEOS)
    ]
    # the channel id is the whole answer; the page is megabytes of markup around it
    assert requested == [VIDEOS]


def test_a_youtube_handle_resolves_through_the_channel_page(authed_client, monkeypatch):
    handle_url = 'https://www.youtube.com/@SkiEssentials'
    serve(monkeypatch, {handle_url: HTML_YOUTUBE})

    body = search(authed_client, '@SkiEssentials', type='youtube').json()

    # no title= on the link tag, so the name falls back to the page's own <title>
    assert [(result['name'], result['feed_url']) for result in body] == [
        ('SkiEssentials - YouTube', VIDEOS)
    ]


def test_a_result_is_typed_by_its_url_not_by_the_wizards_card(authed_client, monkeypatch):
    # the type step is a UI filter and a client is free to be wrong about it
    serve(monkeypatch, {VIDEOS: bodies.ATOM_YOUTUBE})

    body = search(
        authed_client, f'https://www.youtube.com/channel/{CHANNEL_ID}', type='website'
    ).json()

    assert [result['type'] for result in body] == ['youtube']


def test_already_subscribed_is_true_only_for_your_own_feeds(
    authed_client, user, other_user, make_source, make_feed, monkeypatch
):
    serve(monkeypatch, {MEDIUM: bodies.RSS_BLOG})
    source = make_source(feed_url=MEDIUM)
    make_feed(user, source=source)

    assert search(authed_client, MEDIUM).json()[0]['already_subscribed'] is True

    Feed.objects.filter(user=user).delete()
    make_feed(other_user, source=source)

    assert search(authed_client, MEDIUM).json()[0]['already_subscribed'] is False


@pytest.mark.parametrize('query', ['vue tutorials', '', '   '])
def test_a_keyword_finds_nothing_for_now(authed_client, monkeypatch, query):
    # searching our own catalog for it is T11d; until then a keyword touches no network
    requested = serve(monkeypatch, {})

    assert search(authed_client, query).json() == []
    assert requested == []


def test_a_private_address_is_refused_before_a_socket_opens(authed_client):
    # deliberately un-monkeypatched: this is core/fetch.py's guard, reached for real
    assert search(authed_client, 'http://127.0.0.1/feed').json() == []


def test_a_type_the_wizard_cannot_send_is_refused(authed_client, monkeypatch):
    serve(monkeypatch, {})

    assert search(authed_client, MEDIUM, type='podcast').status_code == 422


def test_a_post_url_finds_the_feed_its_section_declares(authed_client, monkeypatch):
    # the gap that mattered: /blog resolved and /blog/meet-nuxi did not, which is backwards
    requested = serve(
        monkeypatch,
        {
            'https://nuxt.com/blog/meet-nuxi': HTML_POST,
            'https://nuxt.com/blog': HTML_SECTION,
        },
    )

    body = search(authed_client, 'https://nuxt.com/blog/meet-nuxi').json()

    assert [(result['name'], result['feed_url']) for result in body] == [
        ('Nuxt Blog', 'https://nuxt.com/blog/rss.xml')
    ]
    # nearest first, and it stops as soon as a page declares something
    assert requested == ['https://nuxt.com/blog/meet-nuxi', 'https://nuxt.com/blog']


def test_a_page_that_declares_a_feed_is_never_walked_past(authed_client, monkeypatch):
    requested = serve(monkeypatch, {'https://nuxt.com/blog': HTML_SECTION})

    search(authed_client, 'https://nuxt.com/blog')

    assert requested == ['https://nuxt.com/blog']


def test_a_dead_ancestor_does_not_end_the_walk(authed_client, monkeypatch):
    # https://nuxt.com/blog is missing from the map, so fetching it 404s
    requested = serve(
        monkeypatch,
        {'https://nuxt.com/blog/meet-nuxi': HTML_POST, 'https://nuxt.com': HTML_SECTION},
    )

    body = search(authed_client, 'https://nuxt.com/blog/meet-nuxi').json()

    assert [result['feed_url'] for result in body] == ['https://nuxt.com/blog/rss.xml']
    assert requested == [
        'https://nuxt.com/blog/meet-nuxi',
        'https://nuxt.com/blog',
        'https://nuxt.com',
    ]


def test_a_walk_that_finds_nothing_still_guesses_from_the_root(authed_client, monkeypatch):
    requested = serve(
        monkeypatch,
        {
            'https://someblog.com/2026/a-post': HTML_BARE,
            'https://someblog.com': HTML_BARE,
            'https://someblog.com/feed': bodies.RSS_BLOG,
        },
    )

    body = search(authed_client, 'https://someblog.com/2026/a-post').json()

    assert [result['feed_url'] for result in body] == ['https://someblog.com/feed']
    # every page above it, then the guesses — the walk is the cheaper half, so it goes first
    assert requested[:3] == [
        'https://someblog.com/2026/a-post',
        'https://someblog.com/2026',
        'https://someblog.com',
    ]


def test_the_walk_is_bounded_but_always_reaches_the_root(authed_client, monkeypatch):
    requested = serve(monkeypatch, {'https://someblog.com/a/b/c/d': HTML_BARE})

    search(authed_client, 'https://someblog.com/a/b/c/d')

    # four levels above it, three fetches — and the one that gets dropped is a middle one,
    # never the root, because that is where a feed most often lives
    assert requested[:4] == [
        'https://someblog.com/a/b/c/d',
        'https://someblog.com/a/b/c',
        'https://someblog.com/a/b',
        'https://someblog.com',
    ]


def test_a_feed_declared_below_head_is_still_found(authed_client, monkeypatch):
    # a parser that stopped at </head> is what made a pasted channel URL find nothing
    serve(monkeypatch, {'https://www.youtube.com/@SkiEssentials': HTML_YOUTUBE})

    body = search(authed_client, '@SkiEssentials', type='youtube').json()

    assert [(result['name'], result['type'], result['feed_url']) for result in body] == [
        ('SkiEssentials - YouTube', 'youtube', VIDEOS)
    ]


def test_a_lone_feed_is_named_after_the_page_not_the_link_tag(authed_client, monkeypatch):
    # title="RSS 2.0" is written for machines; the page's own <title> is written for people
    serve(monkeypatch, {'https://css-tricks.com': HTML_MACHINE_TITLE})

    body = search(authed_client, 'https://css-tricks.com').json()

    assert [result['name'] for result in body] == ['CSS-Tricks']


def test_a_dead_pasted_url_still_searches_the_site_above_it(authed_client, monkeypatch):
    """A stale post URL is still a URL whose site we know, and the site may declare a feed."""
    requested = serve(monkeypatch, {'https://nuxt.com': HTML_SECTION})

    body = search(authed_client, 'https://nuxt.com/blog/gone-in-2024').json()

    assert [result['feed_url'] for result in body] == ['https://nuxt.com/blog/rss.xml']
    assert requested == [
        'https://nuxt.com/blog/gone-in-2024',
        'https://nuxt.com/blog',
        'https://nuxt.com',
    ]
