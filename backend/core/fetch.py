"""The guarded HTTP fetch, for the endpoints that hand a fetched body back to a caller.

Article extraction (core/extract.py) and discovery (core/discover.py) both fetch a URL
somebody else chose and answer with something derived from the response. That is a
different exposure from polling: core/ingest.py only ever stores what it parses, so it
fetches plainly. This side needs a scheme allowlist, a per-hop private-address check and a
size cap — and those rules belong in one module rather than in whichever one happened to
need them first.

The knobs differ per caller and the guard does not: extraction wants HTML only and a hard
2 MB refusal, discovery will read a feed *or* a page and would rather truncate a huge one
than lose it. So everything variable is an argument and everything safety-critical is not.

`requests` does the HTTP here for the same reason it does in ingest — see docs/backend.md
§ Decision log: feedparser's own fetching passes no timeout.
"""

import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import requests

USER_AGENT = 'FeedMe/1.0 (+https://github.com/MartCube/feedme-app)'
ALLOWED_SCHEMES = {'http', 'https'}
# Redirects are followed by hand so every hop gets re-checked — see check_public.
MAX_REDIRECTS = 3
CHUNK = 64 * 1024


class PageUnavailable(Exception):
    """The response never arrived — refused, unreachable, too big, or the wrong type."""


def fetch_url(url, *, accept, timeout, max_bytes, allowed_types=None, truncate=False):
    """Fetch a URL and return its body as bytes.

    `allowed_types` refuses anything outside that set of media types; None accepts whatever
    arrives. A server that sends no content-type at all gets the benefit of the doubt either
    way — plenty of feeds are served like that.
    """
    headers = {'user-agent': USER_AGENT, 'accept': accept}
    for _ in range(MAX_REDIRECTS + 1):
        check_public(url)
        response = requests.get(
            url, headers=headers, timeout=timeout, stream=True, allow_redirects=False
        )
        with response:
            if response.is_redirect:
                location = response.headers.get('location', '')
                if not location:
                    raise PageUnavailable(f'HTTP {response.status_code} with no location')
                url = urljoin(url, location)
                continue
            if response.status_code >= 400:
                raise PageUnavailable(f'HTTP {response.status_code}')
            media_type = response.headers.get('content-type', '').split(';')[0].strip().lower()
            if allowed_types and media_type and media_type not in allowed_types:
                raise PageUnavailable(f'unexpected type: {media_type}')
            return read_capped(response, max_bytes, truncate)

    raise PageUnavailable(f'more than {MAX_REDIRECTS} redirects')


def check_public(url):
    """Refuse anything that isn't a public http(s) address, before a socket is opened.

    The URL is chosen by somebody else — a feed's `post_url` for extraction, the add
    wizard's input box for discovery — and unlike ingest, which only stores what it parses,
    these endpoints hand what comes back to the caller. Without this, pointing one at
    http://169.254.169.254/ reads a cloud metadata service out through our own API.

    Known limit, recorded rather than papered over: this resolves the hostname and then
    requests resolves it again, so a name that answers differently the second time slips
    through. Closing that means pinning the connection to the address vetted here, through
    a custom transport adapter — disproportionate to the exposure, and a partial fix that
    reads as complete would be worse than a stated one.
    """
    parts = urlsplit(url)
    if parts.scheme not in ALLOWED_SCHEMES:
        raise PageUnavailable(f'refusing scheme: {parts.scheme or "(none)"}')
    if not parts.hostname:
        raise PageUnavailable('no host in url')

    try:
        resolved = socket.getaddrinfo(parts.hostname, parts.port, proto=socket.IPPROTO_TCP)
    except (OSError, ValueError) as exc:
        raise PageUnavailable(f'cannot resolve {parts.hostname}') from exc

    for *_, sockaddr in resolved:
        address = ipaddress.ip_address(sockaddr[0])
        # is_global is false for private, loopback, link-local, reserved, multicast and
        # carrier-grade NAT ranges in one check, on both IPv4 and IPv6
        if not address.is_global:
            raise PageUnavailable(f'refusing non-public address: {address}')


def read_capped(response, max_bytes, truncate=False):
    """Read at most max_bytes, without trusting content-length to be honest about it.

    Past the cap the caller either loses the response or keeps the prefix. Extraction
    refuses — something that large is not an article. Discovery truncates: it only reads
    <head>, and a YouTube channel page is megabytes of markup wrapped around the one link
    tag it needs.
    """
    body = bytearray()
    for chunk in response.iter_content(CHUNK):
        body += chunk
        if len(body) > max_bytes:
            if truncate:
                return bytes(body[:max_bytes])
            raise PageUnavailable(f'larger than {max_bytes} bytes')
    return bytes(body)
