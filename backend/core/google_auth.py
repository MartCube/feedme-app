"""Verify the Google id_token the sign-in button hands us.

The one place in the codebase that touches a third party's crypto, and the seam the tests
monkeypatch. Named google_auth rather than google so it can't be confused with the
top-level namespace package it imports from.
"""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2 import id_token

# Reused across requests. Google's public keys are re-fetched on every verification —
# the library caches nothing without a cachecontrol session — which is fine here: this
# runs about once per device per 30 days, the length of a token's sliding window.
_request = Request()


class InvalidGoogleCredential(Exception):
    """Every way a credential can be unusable, collapsed into one thing to catch."""


def verify_google_credential(credential):
    """Return the verified claims (sub, email, …), or raise InvalidGoogleCredential."""
    if not settings.GOOGLE_OAUTH_CLIENT_ID:
        # Not defensive padding: verify_oauth2_token(token, request, None) skips the
        # audience check entirely, so an unset client id would happily accept an id_token
        # minted for somebody else's app.
        raise ImproperlyConfigured('GOOGLE_OAUTH_CLIENT_ID is not set')

    try:
        # Checks the signature, iss, aud and exp itself.
        claims = id_token.verify_oauth2_token(credential, _request, settings.GOOGLE_OAUTH_CLIENT_ID)
    # ValueError: expired, malformed, bad signature, wrong audience. GoogleAuthError:
    # wrong issuer — and it is *not* a ValueError subclass, which is the trap.
    except (ValueError, GoogleAuthError) as error:
        raise InvalidGoogleCredential(str(error)) from error

    if not claims.get('email_verified') or not claims.get('email'):
        # Email is our only identity anchor besides the sub (accounts are linked by it),
        # so a credential we can't trust the email of is one we can't accept at all.
        raise InvalidGoogleCredential('email is not verified')

    return claims
