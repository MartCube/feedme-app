"""Which picture stands for a feed — core/icons.py.

The rule is a ranking, so the tests are about order: what a page declares beats a guess,
bigger beats smaller, and YouTube reads the channel's avatar instead of its own logo.
"""

from core import icons
from core.fetch import PageUnavailable

SITE = 'https://blog.example.com/'
CHANNEL = 'https://www.youtube.com/channel/UCgij'


def page(head):
    return f'<!doctype html><html><head>{head}</head><body></body></html>'.encode()


def test_the_largest_declared_icon_wins():
    body = page(
        '<link rel="icon" href="/favicon-16.png" sizes="16x16">'
        '<link rel="apple-touch-icon" href="/touch.png" sizes="152x152">'
        '<link rel="icon" href="/favicon-32.png" sizes="32x32">'
    )

    assert icons.page_icon(body, SITE) == 'https://blog.example.com/touch.png'


def test_an_apple_touch_icon_without_sizes_counts_as_180():
    """Apple's own default, and larger than any favicon a page bothers to size."""
    body = page(
        '<link rel="icon" href="/favicon-96.png" sizes="96x96">'
        '<link rel="apple-touch-icon" href="/touch.png">'
    )

    assert icons.page_icon(body, SITE) == 'https://blog.example.com/touch.png'


def test_an_svg_that_says_any_size_beats_every_bitmap():
    body = page(
        '<link rel="apple-touch-icon" href="/touch.png" sizes="180x180">'
        '<link rel="icon" href="/icon.svg" sizes="any" type="image/svg+xml">'
    )

    assert icons.page_icon(body, SITE) == 'https://blog.example.com/icon.svg'


def test_shortcut_icon_is_an_icon_and_other_rels_are_not():
    body = page(
        '<link rel="stylesheet" href="/site.css">'
        '<link rel="mask-icon" href="/mask.svg">'
        '<link rel="Shortcut Icon" href="/favicon.ico">'
    )

    assert icons.page_icon(body, SITE) == 'https://blog.example.com/favicon.ico'


def test_a_non_http_icon_is_not_an_icon():
    body = page('<link rel="icon" href="data:image/png;base64,AAAA">')

    assert icons.page_icon(body, SITE) == ''


def test_a_youtube_page_gives_the_channel_avatar_not_youtubes_logo():
    """Every channel page declares YouTube's own favicon; the channel is its og:image.
    Below the head, too — YouTube's metadata lives in the body."""
    body = (
        b'<html><head><link rel="icon" href="https://www.youtube.com/s/favicon.ico"></head>'
        b'<body><meta property="og:image" content="https://yt3.googleusercontent.com/av=s900">'
        b'</body></html>'
    )

    assert icons.page_icon(body, CHANNEL) == 'https://yt3.googleusercontent.com/av=s900'


def test_the_guess_is_the_favicon_at_the_sites_origin():
    assert icons.fallback_icon('https://blog.example.com/tag/vue') == (
        'https://blog.example.com/favicon.ico'
    )


def test_youtube_gets_no_guess():
    """youtube.com/favicon.ico is the YouTube logo — initials say more about a channel."""
    assert icons.fallback_icon(CHANNEL) == ''


def test_site_icon_reads_the_page(monkeypatch):
    monkeypatch.setattr(icons, 'fetch_page', lambda url: page('<link rel="icon" href="/i.png">'))

    assert icons.site_icon(SITE) == 'https://blog.example.com/i.png'


def test_site_icon_guesses_when_the_page_declares_nothing(monkeypatch):
    monkeypatch.setattr(icons, 'fetch_page', lambda url: page(''))

    assert icons.site_icon(SITE) == 'https://blog.example.com/favicon.ico'


def test_site_icon_guesses_when_the_page_is_unreachable():
    # conftest.no_icon_lookups already makes every page unreachable
    assert icons.site_icon(SITE) == 'https://blog.example.com/favicon.ico'


def test_site_icon_of_nothing_fetches_nothing(monkeypatch):
    def fetch_page(url):
        raise PageUnavailable(f'should not have fetched {url}')

    monkeypatch.setattr(icons, 'fetch_page', fetch_page)

    assert icons.site_icon('') == ''
