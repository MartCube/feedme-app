"""Opaque bearer tokens: mint, hash, verify.

Only the SHA-256 hash is stored, so a database leak leaks no live sessions
(docs/backend.md § Auth). Expiry is a sliding 30-day window measured from last_used_at:
an app in daily use never signs the user out, an abandoned one stops working.
"""

import hashlib
import secrets
from datetime import timedelta

from django.utils import timezone
from ninja.security import HttpBearer

from .models import AuthToken

TOKEN_TTL = timedelta(days=30)
# last_used_at is rewritten at most once an hour. The window is 30 days, so an hour of
# staleness can never expire a live token — and every other request stays a single read.
TOUCH_INTERVAL = timedelta(hours=1)


def hash_token(plaintext):
    """SHA-256 hex digest — 64 chars, exactly AuthToken.token_hash's max_length."""
    return hashlib.sha256(plaintext.encode()).hexdigest()


def issue_token(user, device_label=''):
    """Mint a token, store its hash, return the plaintext — the only time it ever exists."""
    plaintext = secrets.token_urlsafe(32)
    AuthToken.objects.create(user=user, token_hash=hash_token(plaintext), device_label=device_label)
    return plaintext


class BearerAuth(HttpBearer):
    """The global guard. ninja puts whatever authenticate() returns on request.auth.

    Returning None means 401: ninja raises AuthenticationError, whose default handler
    answers {"detail": "Unauthorized"}.
    """

    def authenticate(self, request, token):
        now = timezone.now()
        row = AuthToken.objects.select_related('user').filter(token_hash=hash_token(token)).first()
        if row is None or not row.user.is_active or now - row.last_used_at > TOKEN_TTL:
            return None

        if now - row.last_used_at > TOUCH_INTERVAL:
            # .update() not .save(): one UPDATE, no race with a concurrent request
            AuthToken.objects.filter(pk=row.pk).update(last_used_at=now)

        # logout needs the row, not just the user — re-hashing the header to find it
        # again would be a second lookup for nothing
        request.auth_token = row
        return row.user
