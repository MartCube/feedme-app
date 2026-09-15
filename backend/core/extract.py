"""Fetch one post's page and pull the article body out of it.

A post's `summary` is whatever RSS handed us — arbitrary third-party HTML that nothing
sanitises, so the reader shows it as plain text. This module fills the other field,
`Post.article_html`: extracted on the first request for a post and served to everyone
after, since posts are global rows (docs/backend.md § Data model).

Shaped like core/ingest.py on purpose. `fetch_page` is the one function that touches the
network, so a test replaces exactly one symbol, and `extract_article` never raises — a page
that won't extract is a normal answer the reader falls back from, not an error.

Neither library fetches anything. trafilatura can, and the `url=` argument below looks like
it might, but it is used only to absolutise relative links. The HTTP is core/fetch.py's —
guarded, capped and shared with discovery, which fetches a stranger's URL for the same
reason this does.
"""

import logging
from dataclasses import dataclass

import nh3
import requests
import trafilatura

from .fetch import ALLOWED_SCHEMES, PageUnavailable, fetch_url
from .models import Source

logger = logging.getLogger(__name__)

ACCEPT = 'text/html,application/xhtml+xml;q=0.9,*/*;q=0.8'
# (connect, read). Tighter than ingest's read timeout because a reader is watching this
# one — extraction happens inside the request that asked for it.
TIMEOUT = (5, 10)
# What we agree to download. An article is tens of kilobytes; past this it isn't one, so
# the fetch refuses rather than truncating.
MAX_BYTES = 2 * 1024 * 1024
HTML_TYPES = {'text/html', 'application/xhtml+xml'}

# trafilatura's precision/recall knob, deliberately off: it drops borderline blocks, and a
# truncated article reads worse than one carrying a stray heading. One edit if real pages
# argue otherwise.
FAVOR_PRECISION = False

# What survives sanitising. trafilatura already emits a small semantic set and never
# class/id/style/script — but that is a property of its internals, not a promise to us, and
# the frontend renders this field as markup. nh3 turns it into a rule we own. It also drops
# trafilatura's <html><body> document wrapper for free, keeping the children.
ARTICLE_TAGS = {
    'p', 'br', 'a', 'b', 'i', 'strong', 'em', 'sub', 'sup',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'img', 'figure', 'figcaption',
}  # fmt: skip
ARTICLE_ATTRIBUTES = {'a': {'href', 'title'}, 'img': {'src', 'alt', 'title'}}

OK = 'ok'
EMPTY = 'empty'
UNAVAILABLE = 'unavailable'


@dataclass(frozen=True)
class ExtractResult:
    """What happened, for the log. The endpoint reads `post.article_html` itself."""

    status: str
    detail: str = ''


def extract_article(post):
    """Extract this post's article and cache it on the post. Never raises.

    Three stored states: `None` means nobody has tried, `''` means we read the page and
    there was no article in it, and anything else is the article. The first two are told
    apart for admin's sake only — the endpoint retries both, because a page that never
    arrived and a page that arrived empty are equally poor evidence about the article: one
    timeout, a 404 while a site is being deployed, or a challenge page served as 200 should
    not write a post off permanently for every subscriber. The cost is that a truly dead
    or truly empty URL is refetched on each open, which is one bounded call on a rare path.
    """
    if post.source.type == Source.Type.YOUTUBE:
        # A watch page is a JS shell with no article in it. Downloading a megabyte per
        # video open to extract nothing is waste, and summary + Open source is the right
        # treatment for a video anyway.
        return ExtractResult(UNAVAILABLE, 'youtube')

    try:
        body = fetch_page(post.post_url)
    except (PageUnavailable, requests.RequestException) as exc:
        logger.info('extract_article: %s — %s', post.post_url, exc)
        return ExtractResult(UNAVAILABLE, str(exc))

    post.article_html = extract_html(body, post.post_url)
    post.save(update_fields=['article_html'])
    return ExtractResult(OK if post.article_html else EMPTY)


def fetch_page(url):
    """This module's one network call, named so a test can replace exactly this much.

    Everything that makes it safe — the scheme allowlist, the per-hop address check, the
    cap — lives in core/fetch.py; what's left here is the shape an article page has.
    """
    return fetch_url(
        url,
        accept=ACCEPT,
        timeout=TIMEOUT,
        max_bytes=MAX_BYTES,
        allowed_types=HTML_TYPES,
    )


def extract_html(body, url):
    """The article as sanitised HTML, or '' when the page has none to give.

    Handed the raw bytes rather than a decoded string: trafilatura does its own charset
    detection, which beats leaning on requests' guess for pages that mislabel themselves.
    """
    extracted = trafilatura.extract(
        body,
        # relative href/src are absolutised against this; it is never fetched
        url=url,
        output_format='html',
        include_links=True,
        include_images=True,
        favor_precision=FAVOR_PRECISION,
    )
    if not extracted:
        # trafilatura returns None rather than raising when it finds no article
        return ''

    return nh3.clean(
        extracted,
        tags=ARTICLE_TAGS,
        attributes=ARTICLE_ATTRIBUTES,
        # drops a javascript: href rather than the whole <a>
        url_schemes=ALLOWED_SCHEMES,
    ).strip()
