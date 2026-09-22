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

from django.conf import settings

# One 16:9 family for cards and the hero (docs/images.md § Sizes and formats): 480 covers a 1x
# phone, 960 a 2x phone and a 1x desktop pane, 1440 a 3x phone and a 2x pane, 1920 a 2x reading
# measure. imgproxy never enlarges, so asking for a width the source can't fill costs nothing.
WIDTHS = (480, 960, 1440, 1920)
# the bare `src`, for an <img> that ignores srcset
DEFAULT_WIDTH = 960


def post_image(url):
    """Ready `<img>` attributes for a post image, or None when there is nothing to show.

    None for the 63% of posts whose `image_url` is blank, and for a deployment with no key —
    a supported state, like YOUTUBE_API_KEY: the app renders compact cards and nothing breaks.
    """
    if not url or not settings.IMGPROXY_KEY:
        return None
    urls = {width: _signed(url, width) for width in WIDTHS}
    return {
        'src': urls[DEFAULT_WIDTH],
        # the finished attribute, not a list of widths: the sizes are the backend's fact, and
        # sending them as data would let the two sides drift (docs/images.md § Wire contract)
        'srcset': ', '.join(f'{signed} {width}w' for width, signed in urls.items()),
    }


def _signed(url, width):
    # fill + centre gravity: predictable, and it takes exactly the black bars off YouTube's
    # 480x360 hqdefault poster. .webp is named in the path rather than negotiated from Accept,
    # so one URL is one file and no CDN has a Vary header to get wrong.
    path = f'/rs:fill:{width}:{round(width * 9 / 16)}/g:ce/{_b64(url.encode())}.webp'
    stamp = hmac.new(
        bytes.fromhex(settings.IMGPROXY_KEY),
        bytes.fromhex(settings.IMGPROXY_SALT) + path.encode(),
        hashlib.sha256,
    ).digest()
    return f'{settings.IMGPROXY_PUBLIC_URL}/{_b64(stamp)}{path}'


def _b64(raw):
    # unpadded base64url, for both the source URL and the signature — imgproxy's own encoding
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode()
