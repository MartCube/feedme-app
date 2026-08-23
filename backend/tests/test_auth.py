from datetime import timedelta

from django.utils import timezone

from core.auth import TOKEN_TTL, TOUCH_INTERVAL, BearerAuth, hash_token, issue_token
from core.models import AuthToken


def test_issue_token_stores_only_the_hash(user):
    plaintext = issue_token(user, device_label='laptop')

    row = AuthToken.objects.get(user=user)
    assert row.token_hash == hash_token(plaintext)
    assert plaintext not in row.token_hash
    assert row.device_label == 'laptop'


def test_authenticate_returns_the_user(rf, user):
    plaintext = issue_token(user)

    assert BearerAuth().authenticate(rf.get('/'), plaintext) == user


def test_authenticate_rejects_an_unknown_token(rf, user):
    issue_token(user)

    assert BearerAuth().authenticate(rf.get('/'), 'not-a-real-token') is None


def test_authenticate_rejects_a_token_past_the_sliding_window(rf, user):
    plaintext = issue_token(user)
    AuthToken.objects.update(last_used_at=timezone.now() - TOKEN_TTL - timedelta(minutes=1))

    assert BearerAuth().authenticate(rf.get('/'), plaintext) is None


def test_authenticate_rejects_a_deactivated_user(rf, user):
    plaintext = issue_token(user)
    user.is_active = False
    user.save(update_fields=['is_active'])

    assert BearerAuth().authenticate(rf.get('/'), plaintext) is None


def test_use_touches_last_used_at_once_past_the_throttle(rf, user):
    plaintext = issue_token(user)
    stale = timezone.now() - TOUCH_INTERVAL - timedelta(minutes=1)
    AuthToken.objects.update(last_used_at=stale)

    BearerAuth().authenticate(rf.get('/'), plaintext)

    assert AuthToken.objects.get().last_used_at > stale


def test_use_inside_the_throttle_costs_one_query(rf, user, django_assert_num_queries):
    """The throttle is the whole point: one read per request, not a read plus a write."""
    plaintext = issue_token(user)

    with django_assert_num_queries(1):
        BearerAuth().authenticate(rf.get('/'), plaintext)
