"""POST /auth/signup and /auth/login — the email + password way in.

Plus the rule it forced onto Google sign-in: an address nobody verified can't keep a
password once Google proves who owns it.
"""

import pytest

from core import google_auth
from core.models import AuthToken, User

SIGNUP = '/api/v1/auth/signup'
LOGIN = '/api/v1/auth/login'
PASSWORD = 'quiet-reading-list'


def post(client, url, email, password=PASSWORD):
    return client.post(url, {'email': email, 'password': password}, content_type='application/json')


def me(client, token):
    return client.get('/api/v1/me', headers={'authorization': f'Bearer {token}'})


def test_sign_up_creates_an_email_account_and_a_working_token(db, client):
    response = post(client, SIGNUP, '  Reader@Example.com ')

    assert response.status_code == 200
    user = User.objects.get()
    # lowercased whole, not just the domain, so the account can't be split by case later
    assert user.email == 'reader@example.com'
    assert user.check_password(PASSWORD)

    profile = me(client, response.json()['token'])
    assert profile.status_code == 200
    assert profile.json()['provider'] == 'email'


def test_sign_up_refuses_an_email_that_already_has_an_account_in_any_case(client, user):
    # `user` is reader@example.com, a Google/dev account with no password
    response = post(client, SIGNUP, 'READER@example.com')

    assert response.status_code == 409
    assert User.objects.count() == 1
    assert not User.objects.get().has_usable_password()


@pytest.mark.parametrize('password', ['short1', '12345678901', 'password123'])
def test_sign_up_refuses_a_weak_password(db, client, password):
    response = post(client, SIGNUP, 'reader@example.com', password)

    assert response.status_code == 422
    assert response.json()['detail']
    assert not User.objects.exists()


def test_sign_up_refuses_something_that_is_not_an_email(db, client):
    assert post(client, SIGNUP, 'not-an-address').status_code == 422
    assert not User.objects.exists()


@pytest.fixture
def email_user(db):
    return User.objects.create_user(email='reader@example.com', password=PASSWORD)


def test_log_in_with_the_right_password_issues_a_working_token(client, email_user):
    response = post(client, LOGIN, 'Reader@Example.com')

    assert response.status_code == 200
    assert me(client, response.json()['token']).status_code == 200


@pytest.mark.parametrize(
    ('email', 'password'),
    [('reader@example.com', 'wrong-password'), ('nobody@example.com', PASSWORD)],
)
def test_every_refused_log_in_reads_the_same(client, email_user, email, password):
    response = post(client, LOGIN, email, password)

    assert response.status_code == 401
    assert response.json()['detail'] == 'Email or password is wrong.'


def test_an_account_without_a_password_cannot_log_in_with_one(client, user):
    # create_user() without a password stores an unusable one — no string matches it
    assert post(client, LOGIN, user.email, '').status_code == 401
    assert post(client, LOGIN, user.email).status_code == 401


def test_a_disabled_account_cannot_log_in(client, email_user):
    email_user.is_active = False
    email_user.save()

    assert post(client, LOGIN, email_user.email).status_code == 401


def test_log_in_is_throttled_per_client(client, email_user):
    statuses = [
        post(client, LOGIN, email_user.email, 'wrong-password').status_code for _ in range(11)
    ]

    assert statuses[:10] == [401] * 10
    assert statuses[10] == 429


def test_a_forged_forwarded_for_header_does_not_reset_the_throttle(client, email_user):
    # The browser writes X-Forwarded-For itself; a fresh one per guess must not read as a
    # fresh client (settings.NINJA_NUM_PROXIES).
    statuses = [
        client.post(
            LOGIN,
            {'email': email_user.email, 'password': 'wrong-password'},
            content_type='application/json',
            headers={'x-forwarded-for': f'203.0.113.{n}'},
        ).status_code
        for n in range(11)
    ]

    assert statuses[10] == 429


def test_google_sign_in_takes_an_unverified_password_account_over(
    client, email_user, settings, monkeypatch
):
    """Someone registers the owner's address with a password of their own; the owner then
    signs in with Google. The owner gets the account, the password stops working, and every
    session the password opened is gone."""
    settings.GOOGLE_OAUTH_CLIENT_ID = 'test-client-id'
    squatter_token = post(client, LOGIN, email_user.email).json()['token']
    monkeypatch.setattr(
        google_auth.id_token,
        'verify_oauth2_token',
        lambda credential, request, audience: {
            'sub': 'google-sub-1',
            'email': 'reader@example.com',
            'email_verified': True,
        },
    )

    response = client.post(
        '/api/v1/auth/google', {'credential': 'x'}, content_type='application/json'
    )

    assert response.status_code == 200
    email_user.refresh_from_db()
    assert email_user.google_sub == 'google-sub-1'
    assert not email_user.has_usable_password()
    assert me(client, squatter_token).status_code == 401
    assert AuthToken.objects.filter(user=email_user).count() == 1
    assert post(client, LOGIN, email_user.email).status_code == 401
