"""core/fetch.py — what the guarded fetch refuses, and how early it refuses it.

The guard is the point. Article extraction is pointed at a `post_url` that came from a feed
somebody subscribed to; discovery is pointed at whatever was typed into the add wizard. Both
hand what comes back to the caller, which polling never does — so this fetch checks every
redirect hop against the private ranges, caps what it will read, and does it all before a
socket is opened.

Nothing here reaches the network: `requests.get` itself is replaced, and the tests that need
an address use a literal public one so no resolver is involved either.
"""

import socket

import pytest

from core import fetch
from core.fetch import PageUnavailable

# The article fetcher's arguments — the caller with every knob turned on. Individual tests
# override the one they are about.
HTML = {
    'accept': 'text/html',
    'allowed_types': {'text/html', 'application/xhtml+xml'},
    'timeout': (5, 10),
    'max_bytes': 2 * 1024 * 1024,
}


def fetch_html(url, **overrides):
    return fetch.fetch_url(url, **{**HTML, **overrides})


class FakeResponse:
    """Enough of requests.Response for fetch_url. Real ones need a live socket."""

    def __init__(self, status_code, headers=None, chunks=()):
        self.status_code = status_code
        self.headers = headers or {}
        self._chunks = chunks

    @property
    def is_redirect(self):
        return 'location' in self.headers and self.status_code in (301, 302, 303, 307, 308)

    def iter_content(self, size):
        return iter(self._chunks)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def respond(monkeypatch, *responses):
    """Replace requests.get itself, recording the URLs it was called with."""
    called = []

    def get(url, **kwargs):
        called.append(url)
        if not responses:
            raise AssertionError(f'requested {url}, and this test says it should not have')
        return responses[min(len(called) - 1, len(responses) - 1)]

    monkeypatch.setattr(fetch.requests, 'get', get)
    return called


@pytest.mark.parametrize(
    'url',
    [
        'file:///etc/passwd',
        'gopher://example.com/',
        'https://127.0.0.1/admin',
        'http://localhost:8000/admin',
        'http://169.254.169.254/latest/meta-data/',
        'http://10.0.0.5/internal',
        'http://[::1]/admin',
        'https:///no-host',
    ],
)
def test_a_non_public_target_is_refused_before_any_request(url, monkeypatch):
    called = respond(monkeypatch)

    with pytest.raises(PageUnavailable):
        fetch_html(url)

    assert called == []


def test_a_redirect_into_a_private_range_is_refused_at_that_hop(monkeypatch):
    """Following redirects by hand is what buys this: requests would have followed it."""
    called = respond(
        monkeypatch,
        FakeResponse(302, {'location': 'http://169.254.169.254/latest/meta-data/'}),
    )

    with pytest.raises(PageUnavailable, match='non-public'):
        # a literal public address, so the test needs no resolver
        fetch_html('http://93.184.216.34/post')

    assert called == ['http://93.184.216.34/post']


def test_a_redirect_loop_gives_up(monkeypatch):
    called = respond(monkeypatch, FakeResponse(302, {'location': 'http://93.184.216.34/post'}))

    with pytest.raises(PageUnavailable, match='redirects'):
        fetch_html('http://93.184.216.34/post')

    assert len(called) == fetch.MAX_REDIRECTS + 1


def test_a_body_past_the_cap_is_abandoned(monkeypatch):
    respond(monkeypatch, FakeResponse(200, {'content-type': 'text/html'}, [b'x' * fetch.CHUNK] * 3))

    with pytest.raises(PageUnavailable, match='larger than'):
        fetch_html('http://93.184.216.34/post', max_bytes=fetch.CHUNK)


def test_a_type_the_caller_did_not_ask_for_is_not_downloaded(monkeypatch):
    respond(monkeypatch, FakeResponse(200, {'content-type': 'application/pdf'}, [b'%PDF-1.7']))

    with pytest.raises(PageUnavailable, match='unexpected type'):
        fetch_html('http://93.184.216.34/paper')


def test_an_error_status_is_not_parsed_as_a_page(monkeypatch):
    respond(monkeypatch, FakeResponse(403, {'content-type': 'text/html'}, [b'<html>nope</html>']))

    with pytest.raises(PageUnavailable, match='HTTP 403'):
        fetch_html('http://93.184.216.34/post')


def test_a_public_page_is_read_whole(monkeypatch):
    respond(
        monkeypatch,
        FakeResponse(200, {'content-type': 'text/html; charset=utf-8'}, [b'<html>', b'ok</html>']),
    )

    assert fetch_html('http://93.184.216.34/post') == b'<html>ok</html>'


def test_a_name_that_does_not_resolve_is_a_refusal_not_a_crash(monkeypatch):
    def fail(*args, **kwargs):
        raise socket.gaierror('nope')

    monkeypatch.setattr(fetch.socket, 'getaddrinfo', fail)
    called = respond(monkeypatch)

    with pytest.raises(PageUnavailable, match='cannot resolve'):
        fetch_html('https://blog.example.com/p/one')

    assert called == []


def test_a_body_past_the_cap_is_truncated_when_the_caller_asks_for_that(monkeypatch):
    """Discovery's mode: it only reads <head>, so a huge page is still a usable answer."""
    respond(monkeypatch, FakeResponse(200, {'content-type': 'text/html'}, [b'x' * fetch.CHUNK] * 3))

    body = fetch_html('http://93.184.216.34/post', max_bytes=fetch.CHUNK, truncate=True)

    assert body == b'x' * fetch.CHUNK


def test_a_caller_that_names_no_types_takes_whatever_arrives(monkeypatch):
    """Discovery again: it asks for a feed or a page and finds out which by parsing."""
    respond(monkeypatch, FakeResponse(200, {'content-type': 'application/rss+xml'}, [b'<rss/>']))

    assert fetch_html('http://93.184.216.34/feed', allowed_types=None) == b'<rss/>'
