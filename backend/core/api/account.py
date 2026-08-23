"""The signed-in account: who am I, sign out, delete everything."""

from datetime import datetime

from ninja import Router, Schema

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
