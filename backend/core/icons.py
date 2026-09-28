"""Which picture stands for a feed — the rule, shared by discovery and ingest.

docs/images.md § What the app shows: every feed has a face. What a feed says about itself
comes first, but only the part that is square by definition — Atom's `<icon>`. RSS's
`<image>` and Atom's `<logo>` are logos and banners (RSS caps the image at 144 × 400, Atom
asks for 2:1), and a 64 × 64 crop of a banner reads worse than initials. Then the site's own
page: the icons it declares for browsers and home screens, largest first. Then `/favicon.ico`,
unverified — it costs nothing to guess, and a guess that 404s ends as the same initials.

YouTube is its own case: a channel's face is its avatar, which the channel page carries as
`og:image`. Its declared icons are YouTube's, identical for every channel, so a YouTube page
never falls back to them, and there is no favicon guess either — a channel with no avatar
found gets initials, not the YouTube logo.

Shaped like core/extract.py: `fetch_page` is the one network call, so a test replaces exactly
one symbol. Only ingest makes it — discovery already holds the page it read for feed links.
"""

import logging
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import requests

from .fetch import PageUnavailable, fetch_url

logger = logging.getLogger(__name__)

ACCEPT = 'text/html,application/xhtml+xml;q=0.9,*/*;q=0.8'
# (connect, read) — the worker's call, but short anyway: an icon is not worth a slow poll
TIMEOUT = (5, 10)
# Truncating, like discovery: a YouTube channel page carries ~700 KB of inline script before
# it says anything about itself, and what we want is somewhere past it.
MAX_BYTES = 2 * 1024 * 1024
# An apple-touch-icon declared without sizes is 180 × 180 by Apple's own default; a plain
# icon without sizes could be anything, so it ranks below every declared size.
TOUCH_ICON_SIZE = 180
# `sizes="any"` is how an SVG says it scales, which beats any bitmap
ANY_SIZE = 10_000
SIZE = re.compile(r'(\d+)x(\d+)', re.IGNORECASE)


def fetch_page(url):
    """This module's one network call, named so a test can replace exactly this much."""
    return fetch_url(url, accept=ACCEPT, timeout=TIMEOUT, max_bytes=MAX_BYTES, truncate=True)


def page_icon(body, page_url):
    """The icon a page declares for `page_url`'s kind of source, or '' when it has none."""
    parser = _Icons()
    parser.feed(body.decode('utf-8', 'replace'))
    if _is_youtube(page_url):
        href = parser.og_image
    else:
        href = max(parser.icons, default=(0, ''))[1]
    return _absolute_http(href, page_url)


def fallback_icon(site_url):
    """The icon to guess when nothing declared one: `/favicon.ico` at the site's origin.

    '' for YouTube (see the module docstring) and for a site_url that isn't http(s).
    """
    parts = urlsplit(site_url)
    if parts.scheme not in ('http', 'https') or not parts.netloc or _is_youtube(site_url):
        return ''
    return f'{parts.scheme}://{parts.netloc}/favicon.ico'


def site_icon(site_url):
    """Fetch `site_url` and find its icon, falling back to the guess. Never raises.

    For ingest, when a source has no icon of its own: one request, once — the answer is
    stored and a stored icon is never looked up again.
    """
    if not site_url:
        return ''
    try:
        body = fetch_page(site_url)
    except (PageUnavailable, requests.RequestException) as exc:
        logger.info('site_icon: %s — %s', site_url, exc)
        return fallback_icon(site_url)
    return page_icon(body, site_url) or fallback_icon(site_url)


def _is_youtube(url):
    host = (urlsplit(url).hostname or '').lower()
    return host == 'youtube.com' or host.endswith('.youtube.com')


def _absolute_http(href, base_url):
    if not href:
        return ''
    url = urljoin(base_url, href.strip())
    return url if urlsplit(url).scheme in ('http', 'https') else ''


def _size(sizes, relations):
    sizes = (sizes or '').lower()
    if 'any' in sizes.split():
        return ANY_SIZE
    declared = [int(width) for width, _ in SIZE.findall(sizes)]
    if declared:
        return max(declared)
    return TOUCH_ICON_SIZE if any(r.startswith('apple-touch-icon') for r in relations) else 0


class _Icons(HTMLParser):
    """Every icon a page declares, ranked by size, and its og:image.

    Not stopped at </head>, for the same reason core/discover.py's link parser isn't:
    YouTube puts its metadata in the body.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        # (size, href) — max() picks the largest, ties to the later declaration
        self.icons = []
        self.og_image = ''

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == 'link':
            # `icon`, `shortcut icon`, `apple-touch-icon`, `apple-touch-icon-precomposed`
            relations = (attributes.get('rel') or '').lower().split()
            href = (attributes.get('href') or '').strip()
            if href and any(r == 'icon' or r.startswith('apple-touch-icon') for r in relations):
                self.icons.append((_size(attributes.get('sizes'), relations), href))
        elif tag == 'meta' and not self.og_image:
            if (attributes.get('property') or '').lower() == 'og:image':
                self.og_image = (attributes.get('content') or '').strip()
