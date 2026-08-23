import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from core.auth import issue_token


@pytest.fixture
def user(db):
    """A plain app user. No usable password — sign-in is Google-only (backend.md § Auth)."""
    return get_user_model().objects.create_user(email='reader@example.com')


@pytest.fixture
def auth_token(user):
    """The plaintext token for `user` — take this when the test needs the raw string."""
    return issue_token(user, device_label='pytest')


@pytest.fixture
def authed_client(auth_token):
    """A test client sending Authorization: Bearer on every request."""
    return Client(headers={'authorization': f'Bearer {auth_token}'})
