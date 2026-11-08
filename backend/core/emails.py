"""The account emails: confirm your address, reset your password. Their links, and sending them.

A link carries one opaque `token`, `<user>.<proof>`. The proof is Django's own
PasswordResetTokenGenerator, an HMAC over the user's current state and a timestamp under
SECRET_KEY. So nothing is stored, and a link stops working as soon as what it proves changes.
A reset proof covers the password hash: setting a new password spends the link. A
confirmation proof covers `email_verified`, so confirming spends it too.

Sent from the worker (core/tasks.py `send_account_email`), never inline. A slow mail server
can't slow down sign-up, and "forgot password" answers in the same time whether or not the
address has an account.
"""

from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import base36_to_int, urlsafe_base64_decode, urlsafe_base64_encode

from .models import User

# One email of a kind per account per this many seconds. The sign-in throttle limits each
# client IP; this protects the inbox, so a script that rotates addresses still can't bury
# a stranger in reset emails.
SEND_COOLDOWN = 60


class _LinkTokens(PasswordResetTokenGenerator):
    """Django's generator with its own max age. The stock one reads PASSWORD_RESET_TIMEOUT
    for every kind, which must stay ≥ every `max_age` here (settings.py sets it)."""

    max_age = 0

    def check_token(self, user, token):
        if not super().check_token(user, token):
            return False
        # super() has already proved the token well-formed and untampered
        issued = base36_to_int(token.split('-')[0])
        return self._num_seconds(self._now()) - issued <= self.max_age


class _ResetTokens(_LinkTokens):
    # An hour is enough to switch to your inbox and back. Stock hash value: the password
    # hash is in it, so a reset spends its own link and any older one.
    key_salt = 'feedme.reset_password'
    max_age = 60 * 60


class _ConfirmTokens(_LinkTokens):
    # Three days: confirming is never urgent, and an expired link just means "send another".
    key_salt = 'feedme.confirm_email'
    max_age = 3 * 24 * 60 * 60

    def _make_hash_value(self, user, timestamp):
        return f'{user.pk}{user.email}{user.email_verified}{timestamp}'


@dataclass(frozen=True)
class _Kind:
    tokens: PasswordResetTokenGenerator
    path: str  # the app page that opens the link
    subject: str
    heading: str
    body: str
    button: str


KINDS = {
    'confirm': _Kind(
        tokens=_ConfirmTokens(),
        path='/verify-email',
        subject='Confirm your email for FeedMe',
        heading='Confirm your email',
        body='Tap the button to confirm this is your address. The link works for three days.',
        button='Confirm email',
    ),
    'reset': _Kind(
        tokens=_ResetTokens(),
        path='/reset-password',
        subject='Reset your FeedMe password',
        heading='Reset your password',
        body=(
            'Someone asked to reset the password for this address. If it was you, tap the '
            "button within an hour. If it wasn't, ignore this email and nothing changes."
        ),
        button='Choose a new password',
    ),
}


def make_token(user, kind):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    # '.' is in neither alphabet: urlsafe base64 uses -_, Django's proof is base36-hex
    return f'{uid}.{KINDS[kind].tokens.make_token(user)}'


def user_for_token(token, kind):
    """The active user this token proves, or None for anything else: malformed, tampered,
    expired, spent, or a deleted or disabled account. One answer, as in sign-in."""
    uid, _, proof = token.partition('.')
    try:
        pk = int(force_str(urlsafe_base64_decode(uid)))
    except (ValueError, TypeError):
        return None
    user = User.objects.filter(pk=pk, is_active=True).first()
    if user is None or not KINDS[kind].tokens.check_token(user, proof):
        return None
    return user


def send(user, kind):
    """Compose and send one account email. Returns False when it skipped a repeat inside
    the cooldown."""
    key = f'account-email:{kind}:{user.pk}'
    if not cache.add(key, 1, SEND_COOLDOWN):
        return False
    spec = KINDS[kind]
    context = {
        'heading': spec.heading,
        'body': spec.body,
        'button': spec.button,
        'url': f'{settings.APP_URL}{spec.path}?token={make_token(user, kind)}',
    }
    message = EmailMultiAlternatives(
        subject=spec.subject,
        body=render_to_string('emails/account.txt', context),
        to=[user.email],
    )
    message.attach_alternative(render_to_string('emails/account.html', context), 'text/html')
    try:
        message.send()
    except Exception:
        # nothing went out, so the cooldown mustn't stop the actor's retry
        cache.delete(key)
        raise
    return True
