"""The account and its sessions: sign in, sign out, who am I, delete everything — and the
two email links, confirming an address and resetting a password (core/emails.py).

Tagged `user` alongside settings.py — from the outside they are one group (this is my
account and how I like it), even though they are two modules in here.
"""

from datetime import datetime
from typing import Literal

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from ninja import Router, Schema, Status
from ninja.errors import HttpError
from ninja.throttling import AnonRateThrottle

from .. import tasks
from ..auth import issue_token
from ..emails import user_for_token
from ..google_auth import InvalidGoogleCredential, verify_google_credential
from ..models import AuthToken, Source, User
from .errors import ErrorSchema
from .feeds import deactivate_if_orphaned

router = Router(tags=['user'])


class MeSchema(Schema):
    email: str
    created_at: datetime
    # Literal, not str, so the generated TypeScript gets a union (T4's decision).
    provider: Literal['google', 'email']
    # Settings → Account's "Email not confirmed · Resend" row. Nothing is gated on it.
    email_verified: bool

    @staticmethod
    def resolve_provider(obj):
        # Settings → Account renders this as the "Signed in with" row. It describes the
        # *account*, not the session: a linked account that also has a password (the
        # admin superuser, or one set through manage.py changepassword) reads as Google
        # even in a session started with the password. Telling the two apart would need a
        # column on AuthToken, which the row isn't worth.
        return 'google' if obj.google_sub else 'email'

    @staticmethod
    def resolve_email_verified(obj):
        # Google vouches for its addresses. Accounts linked before the column existed carry
        # False, and reading it this way saves a data migration.
        return obj.email_verified or bool(obj.google_sub)


class GoogleSignInSchema(Schema):
    credential: str  # the id_token JWT from Google's callback


class TokenSchema(Schema):
    token: str  # our opaque bearer token — the plaintext, the only time it exists


class EmailSignInSchema(Schema):
    # str, not EmailStr: pydantic's email validator is an extra dependency, and the one
    # check worth making — that the address is unique — is the database's job anyway.
    email: str
    password: str


class ForgotPasswordSchema(Schema):
    email: str


class ResetPasswordSchema(Schema):
    token: str  # the `token` query param of the emailed link, as is
    password: str


class ConfirmEmailSchema(Schema):
    token: str


# Per client IP, shared by both password endpoints' own buckets. Ten a minute is slack
# for a person retyping a password and a wall for a script guessing one. Counted in the
# Django cache (Redis), so it holds across the api's worker processes.
EMAIL_AUTH_THROTTLE = [AnonRateThrottle('10/m')]


@router.post(
    '/auth/google',
    auth=None,
    response={200: TokenSchema, 401: ErrorSchema},
    operation_id='google_sign_in',
)
def google_sign_in(request, payload: GoogleSignInSchema):
    """Trade a verified Google credential for one of our own tokens.

    Returns the token alone, not the profile with it: the frontend sets a token and proves
    it against /me, so answering with just the token lets every way in (this, email log-in,
    sign-up) share that one path.
    """
    try:
        claims = verify_google_credential(payload.credential)
    except InvalidGoogleCredential:
        # Which of the many ways it was unusable isn't the caller's business.
        raise HttpError(401, "Google couldn't verify that sign-in.") from None

    user = _user_for_google(claims['sub'], claims['email'])
    return {'token': issue_token(user, device_label=_device_label(request))}


@router.post(
    '/auth/signup',
    auth=None,
    throttle=EMAIL_AUTH_THROTTLE,
    response={200: TokenSchema, 409: ErrorSchema, 422: ErrorSchema, 429: ErrorSchema},
    operation_id='email_sign_up',
)
def email_sign_up(request, payload: EmailSignInSchema):
    """Create an email + password account and sign it in.

    Answers with the token alone, like /auth/google, so the frontend proves it against /me
    on the same path. The address starts unconfirmed: a confirmation email goes out from the
    worker, and until its link is clicked a later Google sign-in to the same address takes
    the account over (_user_for_google).
    """
    email = User.objects.normalize_email(payload.email.strip()).lower()
    if '@' not in email:
        raise HttpError(422, 'Enter a valid email address.')
    # iexact for the same reason as _user_for_google: rows created before this endpoint
    # (Google, the retired dev tokens) were never lowercased.
    if User.objects.filter(email__iexact=email).exists():
        raise HttpError(409, 'An account with that email already exists. Log in instead.')

    candidate = User(email=email)
    try:
        validate_password(payload.password, user=candidate)
    except DjangoValidationError as error:
        raise HttpError(422, ' '.join(error.messages)) from None

    try:
        user = User.objects.create_user(email=email, password=payload.password)
    except IntegrityError:
        # The exists() above and this insert race on the unique column, same as Google's
        # first sign-in. The loser is told what the winner made true.
        raise HttpError(409, 'An account with that email already exists. Log in instead.') from None

    _send_after_commit(user, 'confirm')
    return {'token': issue_token(user, device_label=_device_label(request))}


@router.post(
    '/auth/login',
    auth=None,
    throttle=EMAIL_AUTH_THROTTLE,
    response={200: TokenSchema, 401: ErrorSchema, 429: ErrorSchema},
    operation_id='email_sign_in',
)
def email_sign_in(request, payload: EmailSignInSchema):
    """Trade an email + password for a token. One refusal for every way it can fail."""
    user = User.objects.filter(email__iexact=payload.email.strip()).first()
    # Unknown email, wrong password, an account with no password (Google-only, dev) and a
    # disabled account all read the same, so the answer never says which addresses exist.
    # check_password on an unusable password is simply False.
    if user is None or not user.is_active or not user.check_password(payload.password):
        raise HttpError(401, 'Email or password is wrong.')
    return {'token': issue_token(user, device_label=_device_label(request))}


@router.post(
    '/auth/password/forgot',
    auth=None,
    throttle=EMAIL_AUTH_THROTTLE,
    response={204: None, 429: ErrorSchema},
    operation_id='forgot_password',
)
def forgot_password(request, payload: ForgotPasswordSchema):
    """Email a reset link, if the address has an account. The answer is 204 either way, so it
    never says which addresses exist. The send happens in the worker, so the timing doesn't
    say either.

    A Google-only account gets a link too: the inbox proves the owner, and the reset gives
    the account its first password.
    """
    user = User.objects.filter(email__iexact=payload.email.strip(), is_active=True).first()
    if user is not None:
        _send_after_commit(user, 'reset')
    return Status(204, None)


@router.post(
    '/auth/password/reset',
    auth=None,
    throttle=EMAIL_AUTH_THROTTLE,
    response={200: TokenSchema, 400: ErrorSchema, 422: ErrorSchema, 429: ErrorSchema},
    operation_id='reset_password',
)
def reset_password(request, payload: ResetPasswordSchema):
    """Set a new password from an emailed link, and sign in with it.

    Every existing session ends: a reset is what you do when a password may be known to
    someone else. The link proved the inbox, so it confirms the address too. The token
    answer is the same shape as sign-in's, for the same one path through /me.
    """
    user = user_for_token(payload.token, 'reset')
    if user is None:
        raise HttpError(400, 'This link has expired or was already used. Ask for a new one.')
    try:
        validate_password(payload.password, user=user)
    except DjangoValidationError as error:
        raise HttpError(422, ' '.join(error.messages)) from None

    with transaction.atomic():
        user.set_password(payload.password)
        user.email_verified = True
        user.save(update_fields=['password', 'email_verified'])
        AuthToken.objects.filter(user=user).delete()
    return {'token': issue_token(user, device_label=_device_label(request))}


@router.post(
    '/auth/email/confirm',
    auth=None,
    response={204: None, 400: ErrorSchema},
    operation_id='confirm_email',
)
def confirm_email(request, payload: ConfirmEmailSchema):
    """Mark the address confirmed from an emailed link.

    No bearer required: the link is often opened on a different device, or in a mail app's
    browser, from the one that signed up. The token is the whole proof.
    """
    user = user_for_token(payload.token, 'confirm')
    if user is None:
        raise HttpError(400, 'This link has expired. Send a new one from Settings → Account.')
    user.email_verified = True
    user.save(update_fields=['email_verified'])
    return Status(204, None)


@router.post(
    '/auth/email/resend',
    response={204: None, 401: ErrorSchema},
    operation_id='resend_confirmation',
)
def resend_confirmation(request):
    """Send the confirmation email again. A no-op for a confirmed address. Repeats are held
    to one a minute by core/emails.py's cooldown rather than refused, so tapping twice is
    harmless."""
    user = request.auth
    if not user.email_verified and not user.google_sub:
        _send_after_commit(user, 'confirm')
    return Status(204, None)


def _send_after_commit(user, kind):
    # After commit, so the worker never looks for a user the request is still writing.
    pk = user.pk
    transaction.on_commit(lambda: tasks.send_account_email.send(pk, kind))


def _device_label(request):
    # AuthToken already carries device_label and admin already renders it, so the device
    # list backend.md § Auth promises collects from every way in.
    return request.headers.get('User-Agent', '')[:200]


def _user_for_google(sub, email):
    """Find, link, or create — the whole identity rule in one place."""
    user = User.objects.filter(google_sub=sub).first()

    # Deliberately not syncing email from the claims when the sub is known: a changed
    # Google address could collide with another row's unique email and turn a routine
    # sign-in into a 500. The sub is the identity; a stale email is the cheaper wrong.

    if user is None:
        # iexact, because EmailField is case-sensitive and normalize_email only lowercases
        # the domain — filter(email=…) would miss Martin@ vs martin@ and create a second
        # account instead of linking.
        existing = User.objects.filter(email__iexact=email).first()
        if existing is not None:
            if existing.google_sub:
                # An email can be reassigned (Workspace domains especially); a sub never
                # changes. Linking onto a row another Google account already claimed would
                # hand the new owner of an address the previous owner's feeds and saves.
                raise HttpError(401, 'That email is already linked to a different Google account.')
            was_confirmed = existing.email_verified
            existing.google_sub = sub
            existing.email_verified = True
            update_fields = ['google_sub', 'email_verified']
            if existing.has_usable_password() and not was_confirmed:
                # An unconfirmed address could have been registered with a password by
                # anyone before its owner arrived. Google has just proved who owns it: the
                # password goes, and every session it opened with it. The owner keeps the
                # account; a squatter keeps nothing. A confirmed address was proved by the
                # same person already, so their password stays alongside Google.
                existing.set_unusable_password()
                update_fields.append('password')
                AuthToken.objects.filter(user=existing).delete()
            existing.save(update_fields=update_fields)
            user = existing
        else:
            try:
                # create_user leaves an unusable password, which is right for an account
                # that only ever signs in with Google.
                user = User.objects.create_user(email=email, google_sub=sub, email_verified=True)
            except IntegrityError:
                # Two simultaneous first sign-ins both miss and both insert on a unique
                # column. transaction.atomic() wouldn't prevent that, only roll it back.
                user = User.objects.get(google_sub=sub)

    if not user.is_active:
        # BearerAuth rejects a deactivated user's token on every request anyway, so
        # issuing one here would mint a token that cannot be used.
        raise HttpError(401, 'That account is disabled.')

    return user


@router.get('/me', response={200: MeSchema, 401: ErrorSchema}, operation_id='get_me')
def me(request):
    return request.auth


@router.post('/auth/logout', response={204: None, 401: ErrorSchema}, operation_id='logout')
def logout(request):
    # revocation is instant — this row *is* the session, which is the whole reason for
    # opaque tokens over JWT (backend.md § Auth). BearerAuth stashed it on the request.
    request.auth_token.delete()
    return Status(204, None)


@router.delete('/me', response={204: None, 401: ErrorSchema}, operation_id='delete_me')
def delete_me(request):
    user = request.auth
    # read before the delete, while the feeds still point at them — the cascade below is the
    # one way feeds vanish without passing through the feed writes, so it owes the same
    # deactivation: a source nobody follows must not go on being polled forever
    sources = list(Source.objects.filter(feeds__user=user).distinct())
    with transaction.atomic():
        # every user-owned table (tokens, feeds and their members, saved, settings) is
        # on_delete=CASCADE; FeedSource.source is PROTECT, which guards the shared Source
        user.delete()
        for source in sources:
            deactivate_if_orphaned(source)
    return Status(204, None)
