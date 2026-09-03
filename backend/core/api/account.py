"""The account and its sessions: sign in, sign out, who am I, delete everything.

Tagged `user` alongside settings.py — from the outside they are one group (this is my
account and how I like it), even though they are two modules in here.
"""

from datetime import datetime
from typing import Literal

from django.db import IntegrityError
from ninja import Router, Schema, Status
from ninja.errors import HttpError

from ..auth import issue_token
from ..google_auth import InvalidGoogleCredential, verify_google_credential
from ..models import User
from .errors import ErrorSchema

router = Router(tags=['user'])


class MeSchema(Schema):
    email: str
    created_at: datetime
    # Literal, not str, so the generated TypeScript gets a union (T4's decision).
    provider: Literal['google', 'dev']

    @staticmethod
    def resolve_provider(obj):
        # Settings → Account renders this as the "Signed in with" row. Note it describes
        # the *account*, not the session: once an account is linked this says 'google'
        # even in a session started by pasting a manage.py issue_token token. Telling the
        # two apart would need a column on AuthToken, which isn't worth one while the dev
        # path is temporary.
        return 'google' if obj.google_sub else 'dev'


class GoogleSignInSchema(Schema):
    credential: str  # the id_token JWT from Google's callback


class TokenSchema(Schema):
    token: str  # our opaque bearer token — the plaintext, the only time it exists


@router.post(
    '/auth/google',
    auth=None,
    response={200: TokenSchema, 401: ErrorSchema},
    operation_id='google_sign_in',
)
def google_sign_in(request, payload: GoogleSignInSchema):
    """Trade a verified Google credential for one of our own tokens.

    Returns the token alone, not the profile with it: the dev-token path already sets a
    token and proves it against /me, so answering with just the token lets both sign-ins
    share that one path on the frontend.
    """
    try:
        claims = verify_google_credential(payload.credential)
    except InvalidGoogleCredential:
        # Which of the many ways it was unusable isn't the caller's business.
        raise HttpError(401, "Google couldn't verify that sign-in.") from None

    user = _user_for_google(claims['sub'], claims['email'])
    # AuthToken already carries device_label and admin already renders it, so the device
    # list backend.md § Auth promises starts collecting from here.
    return {'token': issue_token(user, device_label=request.headers.get('User-Agent', '')[:200])}


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
            existing.google_sub = sub
            existing.save(update_fields=['google_sub'])
            user = existing
        else:
            try:
                # create_user leaves an unusable password, which is right for an account
                # that only ever signs in with Google.
                user = User.objects.create_user(email=email, google_sub=sub)
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
    # every user-owned table (tokens, feeds, folders, saved, settings) is on_delete=CASCADE;
    # Feed.source is PROTECT, which guards the shared Source, not the Feed row
    request.auth.delete()
    return Status(204, None)
