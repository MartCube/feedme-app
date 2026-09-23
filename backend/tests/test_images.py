"""Signed image URLs — docs/images.md § The one rule.

The recipe and the key live in exactly one module, so the bucket (T15d) and the CDN (T15e)
are a change inside it and the wire contract never moves. These tests pin the recipe, the two
states where there is nothing to sign, and the containment itself.
"""

import base64
import pathlib

from django.test import override_settings

from core import images

# 32 bytes each, hex — the shape imgproxy requires. Fixed values, so a signature is stable.
KEY = 'aa' * 32
SALT = 'bb' * 32
IMAGE = 'https://example.com/photo.jpg'
# the shape Reddit's media:thumbnail gives: the size is in the URL, inside the signature
REDDIT = 'https://preview.redd.it/abc.jpeg'

proxy_on = override_settings(
    IMGPROXY_KEY=KEY, IMGPROXY_SALT=SALT, IMGPROXY_PUBLIC_URL='http://localhost:8080'
)


@proxy_on
def test_a_blank_url_has_no_image():
    """63% of posts carry no image, and `image_url` is '' for every one of them."""
    assert images.post_image('') is None


@override_settings(IMGPROXY_KEY='', IMGPROXY_SALT='', IMGPROXY_PUBLIC_URL='')
def test_no_key_means_no_images_rather_than_a_broken_one():
    assert images.post_image(IMAGE) is None


@proxy_on
def test_a_source_that_declares_itself_narrower_than_we_serve_has_no_image():
    """Reddit hands out preview URLs with the size baked in, ?width=140 as often as
    ?width=640, and 43% of the ones we have stored are below our smallest size (measured
    2026-09-22). imgproxy can't enlarge them, so the honest answer is no image at all."""
    assert images.post_image(f'{REDDIT}?width=140&crop=smart&s=abc') is None


@proxy_on
def test_a_source_that_declares_a_width_we_can_use_is_served():
    assert images.post_image(f'{REDDIT}?width=640&crop=smart&s=abc') is not None


@proxy_on
def test_a_declared_width_exactly_at_the_smallest_size_is_served():
    assert images.post_image(f'{REDDIT}?width={images.WIDTHS[0]}') is not None


@proxy_on
def test_a_source_that_declares_nothing_is_served():
    """Most sources say nothing about size — the client's own floor is the backstop there,
    and from T15d the dimensions read at ingest replace both."""
    assert images.post_image(IMAGE) is not None


@proxy_on
def test_a_width_parameter_that_is_not_a_number_is_ignored():
    """`width=large` is not a claim about pixels, so it is not evidence to drop an image on."""
    assert images.post_image(f'{REDDIT}?width=large') is not None


@proxy_on
def test_every_width_is_offered_as_webp_under_the_public_base():
    result = images.post_image(IMAGE)

    pairs = [entry.rsplit(' ', 1) for entry in result['srcset'].split(', ')]

    assert [descriptor for _, descriptor in pairs] == [f'{width}w' for width in images.WIDTHS]
    assert all(url.startswith('http://localhost:8080/') for url, _ in pairs)
    assert all(url.endswith('.webp') for url, _ in pairs)


@proxy_on
def test_src_is_the_default_width_so_a_bare_img_tag_is_right():
    result = images.post_image(IMAGE)

    assert f'{result["src"]} {images.DEFAULT_WIDTH}w' in result['srcset']


@proxy_on
def test_the_path_is_a_sixteen_by_nine_fill_of_the_encoded_source():
    """The recipe imgproxy is being asked for, spelled out: a centre-cropped 16:9 fill of the
    base64url source. `fill-down`, not `fill`: measured against a real YouTube poster, a plain
    `fill` of a source smaller than the requested size hands back the original aspect, bars
    and all (see core/images.py)."""
    src = images.post_image(IMAGE)['src']
    encoded = base64.urlsafe_b64encode(IMAGE.encode()).rstrip(b'=').decode()

    assert src.endswith(f'/rs:fill-down:960:540/g:ce/{encoded}.webp')


@proxy_on
def test_an_article_image_is_fitted_to_the_reading_width_never_cropped():
    """An article's pictures are the author's framing — a diagram cut to 16:9 loses what it
    was there to show. No width floor either: a small inline image is meant to be small."""
    src = images.article_image(f'{REDDIT}?width=140')
    encoded = base64.urlsafe_b64encode(f'{REDDIT}?width=140'.encode()).rstrip(b'=').decode()

    assert src.startswith('http://localhost:8080/')
    assert src.endswith(f'/rs:fit:1920:0/{encoded}.webp')


@override_settings(IMGPROXY_KEY='', IMGPROXY_SALT='', IMGPROXY_PUBLIC_URL='')
def test_no_key_means_no_article_images_either():
    assert images.article_image(IMAGE) is None


@proxy_on
def test_the_signature_covers_the_whole_path():
    """One character of difference must change the stamp, or the signature guards nothing."""
    mine = images.post_image(IMAGE)['src'].rsplit('/rs:', 1)[0]
    theirs = images.post_image('https://example.com/photo.jpeg')['src'].rsplit('/rs:', 1)[0]

    assert mine != theirs


@proxy_on
def test_the_signature_covers_the_salt():
    with override_settings(IMGPROXY_SALT='cc' * 32):
        other = images.post_image(IMAGE)['src']

    assert images.post_image(IMAGE)['src'] != other


def test_only_the_images_module_knows_how_an_image_url_is_made():
    """docs/images.md § The one rule, as a test — modelled on test_search.py's containment of
    the tsvector. If a second module reads an IMGPROXY_* setting, the upgrade seam is gone."""
    core = pathlib.Path(__file__).resolve().parent.parent / 'core'
    exempt = {core / 'images.py'}

    offenders = sorted(
        str(path.relative_to(core))
        for path in core.rglob('*.py')
        if path not in exempt
        and path.parent.name != 'migrations'
        and 'IMGPROXY_' in path.read_text()
    )

    assert offenders == []
