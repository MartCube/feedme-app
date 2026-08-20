import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def user(db):
    """A plain app user. No usable password — sign-in is Google-only (backend.md § Auth)."""
    return get_user_model().objects.create_user(email='reader@example.com')
