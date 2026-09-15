"""GET /posts/{uid}/article — extract once, serve to everyone, fall back cleanly.

Two things are worth pinning here and neither is "trafilatura works". The first is the
caching rule, which is asymmetric on purpose: a page we read and couldn't extract from is
remembered, a page that never arrived is not. The second is that a page which never arrived is
not an error the reader sees — it falls back to summary plus Open source, the same as a
page with no article in it.

The fetch underneath is core/fetch.py's, and so are its tests (test_fetch.py): what this
module owns is the one call named `fetch_page`, which every test below replaces.
"""

import pytest
import requests

from core import extract
from core.models import Source

# Long enough that trafilatura calls it an article rather than boilerplate, with a relative
# link and a relative image so the absolutising in extract_html has something to do.
ARTICLE_PAGE = b"""<!doctype html><html><head><title>The Composition API</title></head>
<body>
  <nav><a href="/tag/vuejs">vuejs</a></nav>
  <article>
    <h1>The Composition API</h1>
    <p>Script setup is the cleanest way to write a Vue component, and the reason has less
    to do with the syntax than with what it stops you from having to name. Options API made
    you declare where every value lived before you could say what it was for.</p>
    <p>Reactivity in depth is the other half of the story. Refs and proxies behave the same
    way from the outside, and the difference only surfaces when you hand one to a function
    that expects to be able to reassign it, which is where most of the confusion starts.</p>
    <p>See <a href="/p/two">the follow-up</a> and <img src="/img/one.png" alt="a diagram"></p>
  </article>
  <footer>&copy; 2026 Some Blog</footer>
</body></html>
"""

# A single-page-app shell: a real 200, no article anywhere in it.
EMPTY_PAGE = (
    b'<!doctype html><html><head><title>App</title></head><body><div id="app"></div></body></html>'
)


def article_request(client, post_uid):
    return client.get(f'/api/v1/posts/{post_uid}/article')


def serve(monkeypatch, *outcomes):
    """Replace the one network call and record every URL it was asked for.

    Each request takes the next outcome and the last one repeats, the same shape
    tests/test_ingest.py uses. An Exception in the list is raised rather than returned.
    Call with no outcomes when the point of the test is that nothing is fetched.
    """
    fetched = []

    def fetch_page(url):
        fetched.append(url)
        outcome = outcomes[min(len(fetched) - 1, len(outcomes) - 1)] if outcomes else None
        if outcome is None:
            raise AssertionError(f'fetched {url}, and this test says it should not have')
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(extract, 'fetch_page', fetch_page)
    return fetched


@pytest.fixture
def post(user, make_source, make_feed, make_post):
    """A post on a website source the caller subscribes to."""
    source = make_source(type=Source.Type.WEBSITE)
    make_feed(user, source=source)
    return make_post(source=source, post_url='https://blog.example.com/p/one')


def test_the_first_open_extracts_the_article(authed_client, post, monkeypatch):
    fetched = serve(monkeypatch, ARTICLE_PAGE)

    body = article_request(authed_client, post.uid).json()

    assert fetched == ['https://blog.example.com/p/one']
    assert body['status'] == 'ok'
    assert 'Script setup is the cleanest way' in body['article_html']
    # the nav and the footer are the page, not the article
    assert 'Some Blog' not in body['article_html']
    post.refresh_from_db()
    assert post.article_html == body['article_html']


def test_relative_links_and_images_come_back_absolute(authed_client, post, monkeypatch):
    """trafilatura resolves them against the url we hand it — nothing here rewrites them."""
    serve(monkeypatch, ARTICLE_PAGE)

    html = article_request(authed_client, post.uid).json()['article_html']

    assert 'https://blog.example.com/p/two' in html
    assert 'https://blog.example.com/img/one.png' in html


def test_a_second_open_is_served_from_the_column(authed_client, post, monkeypatch):
    fetched = serve(monkeypatch, ARTICLE_PAGE)
    first = article_request(authed_client, post.uid).json()

    # no outcomes: the stub now fails the test if it is called at all
    serve(monkeypatch)
    second = article_request(authed_client, post.uid).json()

    assert len(fetched) == 1
    assert second == first


def test_a_page_with_no_article_is_retried_on_the_next_open(authed_client, post, monkeypatch):
    """A 200 with nothing in it is not proof there is nothing: a bot-challenge page or a
    half-deployed site serves exactly that, and the post is one row shared by everyone.
    The '' is still stored — admin can tell "tried, empty" from "never tried" — but the
    reader asks again."""
    fetched = serve(monkeypatch, EMPTY_PAGE, ARTICLE_PAGE)

    first = article_request(authed_client, post.uid).json()
    assert first == {'status': 'unavailable', 'article_html': None}
    post.refresh_from_db()
    assert post.article_html == ''

    second = article_request(authed_client, post.uid).json()
    assert second['status'] == 'ok'
    assert len(fetched) == 2


def test_a_page_that_never_arrived_is_retried_on_the_next_open(authed_client, post, monkeypatch):
    """The asymmetry with the test above: a timeout is not evidence about the article."""
    fetched = serve(monkeypatch, requests.ConnectTimeout('too slow'), ARTICLE_PAGE)

    first = article_request(authed_client, post.uid).json()
    assert first == {'status': 'unavailable', 'article_html': None}
    post.refresh_from_db()
    assert post.article_html is None

    second = article_request(authed_client, post.uid).json()
    assert second['status'] == 'ok'
    assert len(fetched) == 2


def test_a_refused_page_is_unavailable_not_an_error(authed_client, post, monkeypatch):
    serve(monkeypatch, extract.PageUnavailable('HTTP 403'))

    response = article_request(authed_client, post.uid)

    assert response.status_code == 200
    assert response.json() == {'status': 'unavailable', 'article_html': None}


def test_a_youtube_post_is_unavailable_without_a_fetch(
    authed_client, user, make_source, make_feed, make_post, monkeypatch
):
    """A watch page is a JS shell; the fetch would cost a megabyte and return nothing."""
    serve(monkeypatch)
    source = make_source(type=Source.Type.YOUTUBE)
    make_feed(user, source=source)
    video = make_post(source=source, post_url='https://www.youtube.com/watch?v=abc')

    body = article_request(authed_client, video.uid).json()

    assert body == {'status': 'unavailable', 'article_html': None}
    video.refresh_from_db()
    # not remembered either — nothing was learned about the page
    assert video.article_html is None


def test_nothing_dangerous_survives_into_the_stored_html(authed_client, post, monkeypatch):
    """The guarantee is the pipeline's, not one library's, so this asserts on the output.

    trafilatura would strip most of this on its own. nh3 is what makes it a rule we own,
    which is why the next test goes at it directly.
    """
    hostile = ARTICLE_PAGE.replace(
        b'<h1>The Composition API</h1>',
        b'<h1>The Composition API</h1><script>steal()</script>'
        b'<img src=x onerror="steal()"><a href="javascript:steal()">tap</a>',
    )
    serve(monkeypatch, hostile)

    html = article_request(authed_client, post.uid).json()['article_html']

    assert 'steal()' not in html
    assert 'onerror' not in html
    assert 'javascript:' not in html


def test_the_sanitiser_is_what_holds_that_line(monkeypatch):
    """Extraction stands in for a future trafilatura that emits more than it does today."""
    monkeypatch.setattr(
        extract.trafilatura,
        'extract',
        lambda *args, **kwargs: (
            '<html><body><p class="x" onclick="steal()">Kept</p>'
            '<script>steal()</script><a href="javascript:steal()">tap</a>'
            '<a href="https://example.com/ok">fine</a></body></html>'
        ),
    )

    html = extract.extract_html(b'<html></html>', 'https://blog.example.com/p/one')

    assert 'steal' not in html
    assert 'class=' not in html
    # the wrapper goes, its children stay
    assert not html.startswith('<html>')
    assert '<p>Kept</p>' in html
    # the safe href survives, and nh3's default rel comes along with it
    assert '<a href="https://example.com/ok" rel="noopener noreferrer">fine</a>' in html


def test_a_post_you_neither_follow_nor_saved_is_not_readable(authed_client, make_post, monkeypatch):
    serve(monkeypatch)
    stranger = make_post()

    assert article_request(authed_client, stranger.uid).status_code == 404


def test_the_endpoint_needs_a_token(client, post, monkeypatch):
    serve(monkeypatch)

    assert article_request(client, post.uid).status_code == 401
