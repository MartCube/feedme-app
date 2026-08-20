"""The browser only reads a cross-origin response when these headers come back.

Guards the middleware order and CORS_ALLOWED_ORIGINS in settings.py — both easy to
break silently, since nothing else in the API test suite goes through a browser.
"""

NUXT_DEV_ORIGIN = 'http://localhost:3000'


def preflight(client, origin):
    """The OPTIONS request a browser sends before any call carrying an Authorization header."""
    return client.options(
        '/api/v1/health',
        headers={
            'origin': origin,
            'access-control-request-method': 'GET',
            'access-control-request-headers': 'authorization',
        },
    )


def test_preflight_from_the_nuxt_dev_origin_is_allowed(client):
    response = preflight(client, NUXT_DEV_ORIGIN)

    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == NUXT_DEV_ORIGIN


def test_preflight_from_an_unlisted_origin_gets_no_cors_headers(client):
    response = preflight(client, 'http://evil.example')

    assert 'access-control-allow-origin' not in response.headers
