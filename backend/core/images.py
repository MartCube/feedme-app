"""Signed image URLs — the one module that knows how an image URL is made.

docs/images.md § The one rule. The frontend never builds one (the URLs are signed, and a key
on the client is a key in the bundle), and on this side nothing else reads an IMGPROXY_*
setting — a containment test in tests/test_images.py enforces it, the way test_search.py pins
the tsvector to core/search.py. That containment is what makes this the upgrade seam: stage 2
(originals in a bucket) and stage 3 (a CDN, then a paid transformer) are changes inside this
file, with the wire contract and every component untouched.
"""

import base64
import hashlib
import hmac
from urllib.parse import parse_qs, urlsplit

from django.conf import settings

# One 16:9 family for cards and the hero (docs/images.md § Sizes and formats): 480 covers a 1x
# phone, 960 a 2x phone and a 1x desktop pane, 1440 a 3x phone and a 2x pane, 1920 a 2x reading
# measure. imgproxy never enlarges, so asking for a width the source can't fill costs nothing.
WIDTHS = (480, 960, 1440, 1920)
# the bare `src`, for an <img> that ignores srcset
DEFAULT_WIDTH = 960
# an article image, fitted to the 2x reading measure (docs/images.md § Sizes and formats)
ARTICLE_WIDTH = 1920
# a feed icon, square — 2x the 32px slot (docs/images.md § Sizes and formats)
ICON_SIZE = 64


def post_image(url):
    """Ready `<img>` attributes for a post image, or None when there is nothing to show.

    None for the 63% of posts whose `image_url` is blank, for a source that declares itself
    too small to be worth a card (below), and for a deployment with no key — a supported
    state, like YOUTUBE_API_KEY: the app renders compact cards and nothing breaks.
    """
    if not url or not settings.IMGPROXY_KEY or _declared_too_small(url):
        return None
    urls = {width: _signed(url, _card(width)) for width in WIDTHS}
    return {
        'src': urls[DEFAULT_WIDTH],
        # the finished attribute, not a list of widths: the sizes are the backend's fact, and
        # sending them as data would let the two sides drift (docs/images.md § Wire contract)
        'srcset': ', '.join(f'{signed} {width}w' for width, signed in urls.items()),
    }


def article_image(url):
    """A signed `src` for an image inside an extracted article, or None when images are off.

    Fit, never crop, to the 2x reading measure: an article's pictures are the author's own
    framing — a diagram or a screenshot cut to 16:9 loses what it was there to show. One URL
    and no srcset, because the article is sanitised markup the frontend renders as-is.

    No width floor either, unlike post_image: a small image inline in the text is sized to
    sit there, not blown up into a card. imgproxy never enlarges it.
    """
    if not settings.IMGPROXY_KEY:
        return None
    return _signed(url, f'rs:fit:{ARTICLE_WIDTH}:0')


def icon(url):
    """A signed `src` for a feed's icon, or None when there is none or images are off.

    64 × 64, which is 2x the largest slot an icon sits in. The same fill-down crop as the
    cards: a favicon smaller than that comes back at its own size and still square, rather
    than enlarged here — the browser scales a 32px icon into its slot as well as we would.
    imgproxy reads ICO and SVG, which is what favicons are.
    """
    if not url or not settings.IMGPROXY_KEY:
        return None
    return _signed(url, f'rs:fill-down:{ICON_SIZE}:{ICON_SIZE}/g:ce')


def _declared_too_small(url):
    """True when the source URL itself says it is narrower than the smallest size we serve.

    Reddit's RSS is the case this exists for: `media:thumbnail` carries a preview URL with
    the size baked into it — `?width=140` as often as `?width=640` — and the size sits inside
    the `s=` signature, so it can't be raised to ask for a bigger one. 43% of the Reddit
    images in the dev database declare a width under 480 (measured 2026-09-22). imgproxy
    never enlarges, so those arrive at their own size and get blown up into a card a screen
    wide, which reads worse than no image.

    Only `width`, and only when it is a number: a parameter we can't read is not evidence,
    and dropping an image we could have shown is the worse mistake. The feed itself tells us
    nothing — Reddit's media:thumbnail carries a url and no dimensions — so this is the only
    thing knowable before the bytes arrive. T15d reads real dimensions at ingest and replaces
    both this and the frontend's matching read-time floor.
    """
    declared = parse_qs(urlsplit(url).query).get('width', [''])[0]
    return declared.isdigit() and int(declared) < WIDTHS[0]


def _card(width):
    # fill-down + centre gravity: a 16:9 centre crop, which is what takes the black bars off
    # YouTube's 480x360 hqdefault poster. `fill-down` rather than plain `fill` because we never
    # enlarge, and a plain `fill` of a source smaller than the requested size skips the crop
    # altogether and hands back the original aspect — measured against the real poster, which
    # came back 480x360, bars and all. fill-down shrinks the *requested size* to fit the source
    # instead, so the aspect ratio survives and the pixels are still the source's own.
    return f'rs:fill-down:{width}:{round(width * 9 / 16)}/g:ce'


def _signed(url, options):
    # .webp is named in the path rather than negotiated from Accept, so one URL is one file
    # and no CDN has a Vary header to get wrong.
    path = f'/{options}/{_b64(url.encode())}.webp'
    stamp = hmac.new(
        bytes.fromhex(settings.IMGPROXY_KEY),
        bytes.fromhex(settings.IMGPROXY_SALT) + path.encode(),
        hashlib.sha256,
    ).digest()
    return f'{settings.IMGPROXY_PUBLIC_URL}/{_b64(stamp)}{path}'


def _b64(raw):
    # unpadded base64url, for both the source URL and the signature — imgproxy's own encoding
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode()
