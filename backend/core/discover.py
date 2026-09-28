"""Turn what somebody typed into the add wizard into feeds they could subscribe to.

The wizard's input box takes one string and this module decides what it was: a URL, which
we resolve, or a keyword. A keyword under the YouTube card is a Data API search
(core/youtube.py); under the others it finds nothing until T11d searches our own catalog.
There is no web-crawl index behind this and there never will be — that's a Feedly-scale
product (docs/backend.md § Fetching pipeline).

Shaped like core/ingest.py and core/extract.py: `fetch_page` is the one function that
touches the network, so a test replaces exactly one symbol, and `discover` never raises
for a URL — one that refuses to resolve is an empty result the wizard reports, not an
error. The keyword path is the exception, and on purpose: see `_keyword`.

feedparser answers "is this a feed, and what is it called"; it is the same parser every
poll runs through, so a feed the wizard accepts is one ingest can read. What feedparser
does not do is look at a *page* and find the feed on it, which is what `feed_links` is for
— twenty lines of stdlib rather than a dependency, since all it reads is <head>.
"""

import logging
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlunsplit

import feedparser
import requests

from . import icons, youtube
from .fetch import PageUnavailable, fetch_url
from .ingest import feed_metadata
from .models import Source

logger = logging.getLogger(__name__)

ACCEPT = 'application/atom+xml,application/rss+xml,application/xml;q=0.9,text/html;q=0.8,*/*;q=0.7'
# (connect, read). The add wizard is waiting on this, same as the reader is on extraction.
TIMEOUT = (5, 10)
# Truncating, not refusing: a page is read for its link tags and giving up on a big one
# would lose feeds we can see. Sized by the worst real case measured — a YouTube channel
# page carries ~700 KB of inline script before it says anything about itself.
MAX_BYTES = 2 * 1024 * 1024
# Every media type a feed is served as in the wild, including the two generic XML ones —
# plenty of blogs still send text/xml for an Atom document.
FEED_TYPES = {
    'application/rss+xml',
    'application/atom+xml',
    'application/rdf+xml',
    'application/xml',
    'text/xml',
}
# Tried against the site root when a page declares no feed of its own. Ordered by how
# common they are, and short on purpose — this is the miss path, one request each.
COMMON_PATHS = ('/feed', '/rss', '/rss.xml', '/atom.xml', '/index.xml')
# A site declaring more than this many alternates is listing per-tag feeds, not offering
# a choice worth scrolling.
MAX_RESULTS = 5
# How many pages above the pasted one to try. Three covers /blog/2026/some-post, and the
# walk only happens at all when the pasted page declared nothing.
MAX_ANCESTORS = 3
# A URL longer than the column is stored truncated, which would point the feed somewhere
# else entirely — so the wizard shows what subscribing would actually save.
FEED_URL_MAX = Source._meta.get_field('feed_url').max_length

YOUTUBE_FEED = 'https://www.youtube.com/feeds/videos.xml?channel_id={}'
YOUTUBE_CHANNEL = 'https://www.youtube.com/channel/{}'
REDDIT_FEED = 'https://www.reddit.com/r/{}/.rss'
# Reddit's own rule for a subreddit name, so `r/OnePiece`, `/r/OnePiece` and `OnePiece`
# are one case and a sentence with a space in it is not mistaken for one.
SUBREDDIT = re.compile(r'^/?(?:r/)?([A-Za-z0-9_]{2,21})/?$')
SUBREDDIT_PATH = re.compile(r'^/r/([A-Za-z0-9_]{2,21})')
# A channel id is the only YouTube URL shape that needs no page fetch to resolve: the RSS
# endpoint takes it directly. /@handle, /c/… and /user/… go the long way round.
CHANNEL_PATH = re.compile(r'^/channel/(UC[A-Za-z0-9_-]{10,})')
HANDLE = re.compile(r'^@[A-Za-z0-9._-]{3,30}$')


@dataclass(frozen=True)
class Candidate:
    """One subscribable feed, in the shape the wizard shows and POST /feeds accepts.

    Not a Source: nothing is written by discovering. The name is provisional — subscribing
    re-derives it from the feed itself (core/api/feeds.py), so it only has to be good
    enough to pick from a list.
    """

    name: str
    type: str
    feed_url: str
    site_url: str = ''
    icon_url: str = ''


def discover(source_type, query):
    """Everything `query` could mean, as candidates. May be empty.

    Never raises for a URL; a keyword can raise YouTubeUnavailable — see `_keyword`.
    """
    query = (query or '').strip()
    if not query:
        return []

    url = _as_url(query) or _named_url(source_type, query)
    if url is None:
        return _keyword(source_type, query)

    try:
        return _resolve(url)
    except (PageUnavailable, requests.RequestException) as exc:
        logger.info('discover: %s — %s', url, exc)
        return []


def _keyword(source_type, query):
    """A bare name. YouTube can be asked; the other two wait for T11d's catalog search.

    The card decides here, unlike for a URL: `one piece` is a channel search under YouTube
    and nothing under Website, and there is no URL to infer a type from instead.

    Without a key this is T11a again — a name finds nothing, a URL or @handle still
    resolves through the channel page for free. With one, YouTubeUnavailable is let
    through on purpose: "nothing found" for a spent quota is a lie the wizard could not
    tell from a bad search, so core/api/discover.py turns it into a 503 instead.
    """
    if source_type == Source.Type.YOUTUBE and youtube.is_configured():
        return [_from_channel(channel) for channel in youtube.search_channels(query)]
    return []


def _from_channel(channel):
    """A candidate from a Data API hit — the same feed a pasted channel URL resolves to."""
    return Candidate(
        name=channel.title,
        type=Source.Type.YOUTUBE,
        feed_url=YOUTUBE_FEED.format(channel.id),
        site_url=YOUTUBE_CHANNEL.format(channel.id),
        icon_url=channel.thumbnail,
    )


def fetch_page(url):
    """This module's one network call, named so a test can replace exactly this much."""
    return fetch_url(url, accept=ACCEPT, timeout=TIMEOUT, max_bytes=MAX_BYTES, truncate=True)


def probe_feed(url):
    """A candidate if `url` really is a feed, else None. One request, and it may fail."""
    try:
        body = fetch_page(url)
    except (PageUnavailable, requests.RequestException) as exc:
        logger.info('discover: %s — %s', url, exc)
        return None
    return _from_feed(body, url)


def infer_type(feed_url):
    """Which of the three source types a URL is, by host.

    Inferred from the URL rather than taken from the request: the add wizard's type step is
    a UI filter and a client is free to be wrong about it, so a YouTube channel pasted under
    the Website card still comes back typed youtube. `POST /feeds` infers the same way.
    """
    host = (urlsplit(feed_url).hostname or '').lower()
    for domain, source_type in (
        ('youtube.com', Source.Type.YOUTUBE),
        ('reddit.com', Source.Type.REDDIT),
    ):
        if host == domain or host.endswith(f'.{domain}'):
            return source_type
    return Source.Type.WEBSITE


def feed_links(body, base_url):
    """Every feed a page declares, plus its <title>, from `<link rel="alternate">` tags.

    Decoded as UTF-8 with replacement rather than by sniffing the page's charset: hrefs are
    ASCII either way, so the worst a mislabelled page costs is a mangled character in a
    name subscribing overwrites anyway — and the body may be truncated mid-character.
    """
    parser = _FeedLinks()
    parser.feed(body.decode('utf-8', 'replace'))
    links = [(urljoin(base_url, href), title) for href, title in parser.links]
    return links, parser.title


def _resolve(url):
    """One URL, in the cheapest order that can answer it."""
    subreddit = _subreddit_of(url)
    if subreddit:
        # /r/<name>/.rss is the whole rule; fetching the HTML page first would buy nothing
        candidate = probe_feed(REDDIT_FEED.format(subreddit))
        return [candidate] if candidate else []

    channel_id = _channel_of(url)
    if channel_id:
        candidate = probe_feed(YOUTUBE_FEED.format(channel_id))
        return [candidate] if candidate else []

    # Tolerant on purpose: a pasted URL that 404s is still a URL we know the site of, and
    # the site root may well declare a feed. A dead link should cost the walk, not the search.
    body = _try_fetch(url)

    if body is not None:
        # somebody who already knew the feed URL — the one case the wizard handled before T11a
        pasted = _from_feed(body, url)
        if pasted:
            return [pasted]

    for page, page_body in _pages_upward(url, body):
        links, page_title = feed_links(page_body, page)
        if links:
            return _candidates(links, page, page_title, page_body)

    return _guess_paths(url)


def _pages_upward(url, body):
    """The pasted page, then each ancestor path — nearest first, up to the site root.

    An article URL is what somebody actually has in the address bar when they decide to
    subscribe, and an article page routinely declares no feed while the section index above
    it does: https://nuxt.com/blog/meet-nuxi declares none, https://nuxt.com/blog declares
    /blog/rss.xml. Only walked when the pasted page itself came up empty, so the tidy case
    still costs one request.
    """
    if body is not None:
        yield url, body
    for ancestor in _ancestors(url):
        fetched = _try_fetch(ancestor)
        if fetched is not None:
            yield ancestor, fetched


def _ancestors(url):
    """Every path above `url`, nearest first, ending at the site root.

    Capped at MAX_ANCESTORS fetches — but the root is kept whatever gets dropped, since a
    deep URL like /blog/2026/01/some-post has date archives between it and the one page
    that actually declares a feed.
    """
    segments = [segment for segment in urlsplit(url).path.split('/') if segment]
    origin = _origin(url)
    levels = [
        origin + ''.join(f'/{segment}' for segment in segments[:depth])
        for depth in range(len(segments) - 1, -1, -1)
    ]
    if len(levels) > MAX_ANCESTORS:
        levels = levels[: MAX_ANCESTORS - 1] + [origin]
    return levels


def _try_fetch(url):
    """Like fetch_page, but a miss is an answer: one dead ancestor ends no search."""
    try:
        return fetch_page(url)
    except (PageUnavailable, requests.RequestException) as exc:
        logger.info('discover: %s — %s', url, exc)
        return None


def _candidates(links, page, page_title, page_body):
    """The declared feeds, named as well as a page allows.

    Returned unprobed: subscribing fetches for real and takes the true title from the feed,
    so confirming each one here would multiply the wait to improve a label.

    The page's own <title> beats the link's `title=` attribute when there is only one feed,
    because that attribute is written for machines and says things like "RSS" or "RSS 2.0".
    With several it wins instead — that is where it stops being decoration and becomes the
    only thing separating a site's posts feed from its comments feed.
    """
    prefer_link_title = len(links) > 1
    # read off the page we already hold, so the icon costs no request of its own
    icon_url = icons.page_icon(page_body, page) or icons.fallback_icon(page)
    return _dedupe(
        Candidate(
            name=(title or page_title if prefer_link_title else page_title or title) or _host(page),
            type=infer_type(href),
            feed_url=href[:FEED_URL_MAX],
            site_url=_origin(page),
            icon_url=icon_url,
        )
        for href, title in links
    )


def _guess_paths(url):
    """The fallback for a page that declares nothing: try where feeds usually live.

    Static-site generators ship a working feed and routinely forget the <link> tag, which
    is where most "that blog has no feed" complaints actually come from. Up to five extra
    requests, on the miss path only, and the first hit wins.
    """
    root = _origin(url)
    for path in COMMON_PATHS:
        candidate = probe_feed(root + path)
        if candidate:
            return [candidate]
    return []


def _from_feed(body, feed_url):
    """A candidate built from a parsed feed, or None if these bytes weren't one.

    `version` rather than entries: feedparser sets it only when it recognised a feed
    format, so a brand-new blog whose feed is still empty is correctly a feed, and an HTML
    page is correctly not one.
    """
    parsed = feedparser.parse(body, response_headers={'content-location': feed_url})
    if not parsed.get('version'):
        return None

    metadata = feed_metadata(parsed.feed)
    site_url = metadata['site_url'] or _origin(feed_url)
    return Candidate(
        name=metadata['title'].strip() or _host(feed_url),
        type=infer_type(feed_url),
        feed_url=feed_url[:FEED_URL_MAX],
        site_url=site_url,
        # no page in hand here, so a feed with no <icon> of its own gets the free guess;
        # subscribing looks the page up properly (core/icons.py)
        icon_url=metadata['icon_url'] or icons.fallback_icon(site_url),
    )


def _as_url(query):
    """`query` as an http(s) URL, or None. A bare hostname counts — people paste those."""
    if any(character.isspace() for character in query):
        return None
    parts = urlsplit(query if '//' in query else f'//{query}', scheme='https')
    if parts.scheme not in ('http', 'https') or not parts.hostname or '.' not in parts.hostname:
        return None
    return urlunsplit(parts)


def _named_url(source_type, query):
    """The two names that resolve without a search: a subreddit, and a YouTube handle."""
    if source_type == Source.Type.REDDIT:
        match = SUBREDDIT.match(query)
        if match:
            return REDDIT_FEED.format(match.group(1))
    if source_type == Source.Type.YOUTUBE and HANDLE.match(query):
        return f'https://www.youtube.com/{query}'
    return None


def _subreddit_of(url):
    match = SUBREDDIT_PATH.match(urlsplit(url).path)
    return match.group(1) if match and infer_type(url) == Source.Type.REDDIT else None


def _channel_of(url):
    match = CHANNEL_PATH.match(urlsplit(url).path)
    return match.group(1) if match and infer_type(url) == Source.Type.YOUTUBE else None


def _dedupe(candidates):
    seen, kept = set(), []
    for candidate in candidates:
        if candidate.feed_url not in seen:
            seen.add(candidate.feed_url)
            kept.append(candidate)
    return kept[:MAX_RESULTS]


def _origin(url):
    parts = urlsplit(url)
    return f'{parts.scheme}://{parts.netloc}'


def _host(url):
    return (urlsplit(url).hostname or url).removeprefix('www.')


class _FeedLinks(HTMLParser):
    """Collects every feed a page declares, and its title.

    Every feed it lists, not just the first: a WordPress blog declares its posts feed and
    its comments feed with the same rel and type, and which of the two you meant is yours
    to say, not ours to guess.

    Deliberately not restricted to <head>, though that is where the tag belongs. YouTube
    closes <head> after ~700 KB of inline script and puts its <title> and its
    `videos.xml?channel_id=…` link *below* it, in the body — stopping at </head> is exactly
    what made a pasted channel URL resolve to nothing.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.title = ''
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == 'title':
            self._in_title = True
        elif tag == 'link':
            attributes = dict(attrs)
            # rel is a space-separated list, and casing is the author's business
            relations = (attributes.get('rel') or '').lower().split()
            media_type = (attributes.get('type') or '').strip().lower()
            href = (attributes.get('href') or '').strip()
            if href and media_type in FEED_TYPES and 'alternate' in relations:
                self.links.append((href, (attributes.get('title') or '').strip()))

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False

    def handle_data(self, data):
        # the first title wins: a document can carry more than one, and the outer one is
        # the page's own
        if self._in_title and not self.title:
            self.title = data.strip()
