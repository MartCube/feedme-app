"""The signed-in account: who am I, sign out, delete everything."""

from datetime import datetime

from ninja import Router, Schema, Status

from .errors import ErrorSchema

router = Router()


class MeSchema(Schema):
    email: str
    created_at: datetime
    provider: str

    @staticmethod
    def resolve_provider(obj):
        # Settings → Account renders this as the "Signed in with" row. Dev tokens from
        # manage.py issue_token have no google_sub; T8 makes 'google' the only value.
        return 'google' if obj.google_sub else 'dev'


@router.get('/me', response={200: MeSchema, 401: ErrorSchema})
def me(request):
    return request.auth


@router.post('/auth/logout', response={204: None, 401: ErrorSchema})
def logout(request):
    # revocation is instant — this row *is* the session, which is the whole reason for
    # opaque tokens over JWT (backend.md § Auth). BearerAuth stashed it on the request.
    request.auth_token.delete()
    return Status(204, None)


@router.delete('/me', response={204: None, 401: ErrorSchema})
def delete_me(request):
    # every user-owned table (tokens, feeds, folders, saved, settings) is on_delete=CASCADE;
    # Feed.source is PROTECT, which guards the shared Source, not the Feed row
    request.auth.delete()
    return Status(204, None)
