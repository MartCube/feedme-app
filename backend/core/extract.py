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
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import lxml.html
import nh3
import requests
import trafilatura

from . import images
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

# An <img> as nh3 serialises it: every value double-quoted, with `"` and `>` escaped inside
# it, so a tag ends at the first `>` and ` src="` can only ever be the attribute itself.
# Sound only over nh3's own output, which is why proxy_images runs it on the second pass.
IMG_TAG = re.compile(r'<img\b[^>]*>')

# What a link to a bigger copy of a picture ends in. A "click to enlarge" link often lives on
# a CDN host, so a link that lands on an image file is the author's picture, never decoration.
IMAGE_SUFFIXES = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif')

# Words in a block's class, id, data-testid or aria-label that mark it as the page's furniture
# rather than the article — related posts, newsletter boxes, share bars, comments. Matched as
# the start of a word, so Jetpack's `jp-relatedposts` and `sharedaddy` count. trafilatura keeps
# some of these: Cointelegraph's "More on the subject" is other posts' covers, each twice.
BOILERPLATE_ATTRIBUTES = ('class', 'id', 'data-testid', 'aria-label')
BOILERPLATE_WORDS = (
    'related', 'recommend', 'newsletter', 'subscribe', 'subscription',
    'share', 'promo', 'affiliate', 'comment',
)  # fmt: skip
# ...and words that only mean it as a pair: `more-on-subject`, `read-next`, `also-read`
BOILERPLATE_PAIRS = (('more', 'on'), ('read', 'next'), ('also', 'read'))
# What a labelled block can be: a container or a paragraph (9to5Mac's
# `<p class="disclaimer-affiliate">`), never the document, the article or a heading.
# A heading because WordPress ids one by its own words — "…for Apple Creator Studio
# subscribers" carries `id="h-…-subscribers"`. A share button or a decorative image because
# trafilatura drops those itself, and taking one out first can tip which part of the page it
# settles on: one 9-character "Share" button gone, and CoinDesk's article came back with the
# site's numbered most-read list attached.
BOILERPLATE_TAGS = {'section', 'div', 'aside', 'nav', 'footer', 'form', 'ul', 'ol', 'p'}

# The blocks a repeat is looked for in, and the shortest text that counts as one: a page that
# renders its standfirst or a quote twice repeats a sentence, while "Yes." twice is just prose.
# Not list items: one bullet under each of three products' lists is the author's structure.
TEXT_BLOCKS = ('p', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6')
MIN_REPEAT = 40
_IS_BLOCK = ' or '.join(f'self::{tag}' for tag in TEXT_BLOCKS)
# innermost blocks only: a <blockquote> and the <p> inside it say the same thing once, not twice
LEAF_BLOCKS = f'//*[{_IS_BLOCK}][not(.//*[{_IS_BLOCK}])]'

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

    post.article_html = extract_html(body, post.post_url, post.title)
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


def extract_html(body, url, title=''):
    """The article as sanitised HTML, or '' when the page has none to give.

    Handed the raw bytes rather than a decoded string: trafilatura does its own charset
    detection, which beats leaning on requests' guess for pages that mislabel themselves.

    `title` is the post's, which the reader already shows above the article — its copy in
    the text goes.
    """
    tree = trafilatura.load_html(body)
    if tree is None:
        return ''
    _drop_offsite_image_links(tree, url)
    _drop_boilerplate(tree)

    extracted = trafilatura.extract(
        tree,
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

    # nh3 last, so whatever the tidying hands on, the sanitiser still has the final word
    return nh3.clean(
        _drop_repeats(extracted, title),
        tags=ARTICLE_TAGS,
        attributes=ARTICLE_ATTRIBUTES,
        # drops a javascript: href rather than the whole <a>
        url_schemes=ALLOWED_SCHEMES,
    ).strip()


def _drop_offsite_image_links(tree, url):
    """Remove the page's linked-out pictures before trafilatura reads it.

    A badge, an ad or a follow-us button is an image wrapped in a link to somebody else's
    site, sitting inside the article column — and trafilatura keeps the image while dropping
    the link, so on our side it turns into a big unexplained picture (9to5mac's "add as a
    preferred source on Google", a retina file served at twice the size it's drawn at). An
    author's own picture is either unlinked, linked within the site, or linked to its own
    full-size file, and none of those match. Done here, on the page, because the link is the
    only evidence and it's gone by the time trafilatura is done.
    """
    for link in tree.xpath('//a[@href][.//img]'):
        if link.text_content().strip():
            continue
        target = urlsplit(urljoin(url, link.get('href')))
        if _same_site(target.hostname, urlsplit(url).hostname):
            continue
        if target.path.lower().endswith(IMAGE_SUFFIXES):
            continue
        link.drop_tree()


def _drop_boilerplate(tree):
    """Remove the blocks the page itself labels as not the article, before trafilatura reads it.

    The label is the evidence, and it's on the page only: trafilatura's output carries no
    class or id. The risk is a wrapper that happens to carry one of the words —
    `<div class="post has-related-posts">` — so a block is kept, whatever it's called, when it
    holds the page's headline or at least half of its paragraphs.
    """
    headline = tree.find('.//h1')
    paragraphs = len(tree.findall('.//p'))
    for element in tree.xpath('//*[@class or @id or @data-testid or @aria-label]'):
        if element.tag not in BOILERPLATE_TAGS or not _labelled_boilerplate(element):
            continue
        if headline is not None and headline in element.iterdescendants():
            continue
        if paragraphs and len(element.findall('.//p')) * 2 >= paragraphs:
            continue
        element.drop_tree()


def _labelled_boilerplate(element):
    label = ' '.join(element.get(attribute, '') for attribute in BOILERPLATE_ATTRIBUTES)
    words = [word for word in re.split(r'[\s_-]+', label.lower()) if word]
    if any(word.startswith(BOILERPLATE_WORDS) for word in words):
        return True
    pairs = set(zip(words, words[1:], strict=False))
    return any(pair in pairs for pair in BOILERPLATE_PAIRS)


def _drop_repeats(extracted, title):
    """trafilatura's article without what it says twice: the post's own title, a block of
    text it already had, a picture it already showed.

    Pages render the same thing more than once for different layouts — a mobile and a desktop
    copy of a list, a standfirst repeated as the first paragraph, an embedded post quoted in
    full beside its own preview — and trafilatura keeps every copy.
    """
    root = lxml.html.fromstring(extracted)
    heading = _normalised(title)
    seen_text = set()
    for block in root.xpath(LEAF_BLOCKS):
        text = _normalised(block.text_content())
        if heading and block.tag.startswith('h') and text == heading:
            block.drop_tree()
        elif len(text) >= MIN_REPEAT and text in seen_text:
            block.drop_tree()
        else:
            seen_text.add(text)
    seen_files = set()
    for image in root.xpath('//img[@src]'):
        file = _file(image.get('src'))
        if file in seen_files:
            image.drop_tree()
        seen_files.add(file)
    return lxml.html.tostring(root, encoding='unicode')


def _normalised(text):
    return ' '.join(text.split()).casefold()


def _same_site(host, other):
    """Both hosts belong to one site: blog.example.com, cdn.example.com and example.com do."""
    return bool(host and other) and _site(host) == _site(other)


def _site(host):
    """The domain a host was registered under — its last two labels, or three under a
    two-letter country suffix with a short second level (`bbc.co.uk`, `abc.net.au`). A rule
    of thumb rather than the public suffix list, which is a dependency for a cosmetic call."""
    labels = host.lower().split('.')
    keep = 3 if len(labels) > 2 and len(labels[-1]) == 2 and len(labels[-2]) <= 3 else 2
    return '.'.join(labels[-keep:])


def proxy_images(html, lead=''):
    """The article with every `<img src>` pointed at the image proxy, for serving.

    Done at read time and never written back: the column keeps the source's URLs, so a key
    rotation or a recipe change can't break every cached article (docs/images.md). A second
    nh3 pass with the same allowlist does the rewrite, since its attribute filter hands us
    each `src` already unescaped and escapes whatever we return.

    An image that can't be proxied goes, tag and all, rather than leaving an `<img>` with no
    `src` for the browser to draw as broken: a src that isn't an absolute http(s) URL (a
    relative one trafilatura couldn't resolve; a data: URI was already dropped at
    extraction), and every image when the proxy has no key — images are off, as on the cards.

    `lead` is the picture the post page already shows above the title, when it shows one. A
    blog's lead image is usually the article's first picture too, so its copy in the text goes
    — matched on the file, not the whole URL, since the two often ask for different sizes.
    """
    lead_file = _file(lead) if lead else None

    def proxy_src(tag, attribute, value):
        if (tag, attribute) != ('img', 'src'):
            return value
        parts = urlsplit(value)
        if parts.scheme not in ALLOWED_SCHEMES or not parts.netloc:
            return None
        if _file(value) == lead_file:
            return None
        return images.article_image(value)

    cleaned = nh3.clean(
        html,
        tags=ARTICLE_TAGS,
        attributes=ARTICLE_ATTRIBUTES,
        url_schemes=ALLOWED_SCHEMES,
        attribute_filter=proxy_src,
    )
    return IMG_TAG.sub(lambda tag: tag[0] if ' src="' in tag[0] else '', cleaned)


def _file(url):
    """Which file a URL names, whatever size its query asks for: host and path."""
    parts = urlsplit(url)
    return ((parts.hostname or '').removeprefix('www.'), parts.path)
