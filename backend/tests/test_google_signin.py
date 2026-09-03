"""POST /auth/google — verifying a credential, and the identity rule behind it.

What is monkeypatched is the *library* boundary (core.google_auth.id_token.verify_oauth2_token),
not our own wrapper, so the client-id guard, the two exception families and the
verified-email rule all stay under test rather than being stubbed past.
"""

import pytest
from django.core.exceptions import ImproperlyConfigured
from google.auth.exceptions import GoogleAuthError

from core import google_auth
from core.models import AuthToken, User

CLIENT_ID = 'test-client-id.apps.googleusercontent.com'
URL = '/api/v1/auth/google'


@pytest.fixture(autouse=True)
def google_client_id(settings):
    settings.GOOGLE_OAUTH_CLIENT_ID = CLIENT_ID


def claims(sub='google-sub-1', email='reader@example.com', **overrides):
    return {'sub': sub, 'email': email, 'email_verified': True, **overrides}


@pytest.fixture
def google(monkeypatch):
    """Stand in for Google: answer with claims, or raise the way the library would."""

    def _respond_with(result):
        def fake_verify(credential, request, audience):
            # The audience is the whole point of the guard — pin that we pass it.
            assert audience == CLIENT_ID
            if isinstance(result, Exception):
                raise result
            return result

        monkeypatch.setattr(google_auth.id_token, 'verify_oauth2_token', fake_verify)

    return _respond_with


def sign_in(client, credential='any-credential', **extra):
    return client.post(URL, {'credential': credential}, content_type='application/json', **extra)


def test_a_new_google_account_creates_a_user_and_a_working_token(db, client, google):
    google(claims())

    response = sign_in(client)

    assert response.status_code == 200
    user = User.objects.get(google_sub='google-sub-1')
    assert user.email == 'reader@example.com'

    token = response.json()['token']
    me = client.get('/api/v1/me', headers={'authorization': f'Bearer {token}'})
    assert me.status_code == 200
    assert me.json()['provider'] == 'google'


def test_signing_in_twice_is_two_sessions_for_one_account(db, client, google):
    google(claims())

    first = sign_in(client).json()['token']
    second = sign_in(client).json()['token']

    assert first != second
    assert User.objects.count() == 1
    assert AuthToken.objects.count() == 2


def test_an_unclaimed_account_with_the_same_email_is_linked(client, google, user, make_feed):
    feed = make_feed(user, name='Kept through the link')
    google(claims(email=user.email))

    assert sign_in(client).status_code == 200

    user.refresh_from_db()
    assert user.google_sub == 'google-sub-1'
    assert User.objects.count() == 1
    assert list(user.feeds.all()) == [feed]


def test_linking_matches_the_email_case_insensitively(db, client, google):
    """EmailField is case-sensitive and normalize_email only lowercases the domain, so a
    plain filter(email=…) would create a second account here instead of linking."""
    existing = User.objects.create_user(email='Martin@Example.com')
    google(claims(email='martin@example.com'))

    assert sign_in(client).status_code == 200

    existing.refresh_from_db()
    assert existing.google_sub == 'google-sub-1'
    assert User.objects.count() == 1


def test_an_email_claimed_by_another_google_account_is_refused(db, client, google):
    """An email can be reassigned; a sub never changes. Linking here would hand the new
    owner of an address the previous owner's account."""
    owner = User.objects.create_user(email='shared@example.com', google_sub='the-first-sub')
    google(claims(sub='a-second-sub', email='shared@example.com'))

    response = sign_in(client)

    assert response.status_code == 401
    assert 'different Google account' in response.json()['detail']
    owner.refresh_from_db()
    assert owner.google_sub == 'the-first-sub'
    assert User.objects.count() == 1


def test_a_changed_google_email_does_not_rewrite_the_stored_one(db, client, google):
    existing = User.objects.create_user(email='old@example.com', google_sub='stable-sub')
    google(claims(sub='stable-sub', email='new@example.com'))

    assert sign_in(client).status_code == 200

    existing.refresh_from_db()
    assert existing.email == 'old@example.com'
    assert User.objects.count() == 1


def test_an_unverified_email_is_refused(db, client, google):
    google(claims(email_verified=False))

    assert sign_in(client).status_code == 401
    assert not User.objects.exists()


def test_a_credential_the_library_rejects_is_a_401(db, client, google):
    google(ValueError('Token expired'))

    response = sign_in(client)

    assert response.status_code == 401
    assert response.json() == {'detail': "Google couldn't verify that sign-in."}
    assert not User.objects.exists()


def test_a_bad_issuer_is_a_401_not_a_crash(db, client, google):
    """GoogleAuthError is not a ValueError subclass — catching only ValueError turns a
    wrong-issuer token into a 500."""
    google(GoogleAuthError('Wrong issuer.'))

    assert sign_in(client).status_code == 401
    assert not User.objects.exists()


def test_a_disabled_account_gets_no_token(db, client, google):
    User.objects.create_user(email='banned@example.com', google_sub='banned-sub', is_active=False)
    google(claims(sub='banned-sub', email='banned@example.com'))

    assert sign_in(client).status_code == 401
    assert not AuthToken.objects.exists()


def test_signing_in_is_the_one_route_open_to_a_caller_with_no_token(db, client, google):
    google(claims())

    assert sign_in(client).status_code == 200
    # …and the global guard is still on everything else.
    assert client.get('/api/v1/me').status_code == 401


def test_the_token_records_the_device_it_was_issued_to(db, client, google):
    google(claims())

    sign_in(client, headers={'user-agent': 'Mozilla/5.0 (pytest)'})

    assert AuthToken.objects.get().device_label == 'Mozilla/5.0 (pytest)'


def test_an_unset_client_id_never_reaches_the_verifier(settings, monkeypatch):
    """verify_oauth2_token(token, request, None) skips the audience check entirely, so an
    unconfigured server would accept an id_token minted for somebody else's app."""
    settings.GOOGLE_OAUTH_CLIENT_ID = ''

    def explode(*args, **kwargs):
        raise AssertionError('the verifier must not be called without an audience')

    monkeypatch.setattr(google_auth.id_token, 'verify_oauth2_token', explode)

    with pytest.raises(ImproperlyConfigured):
        google_auth.verify_google_credential('any-credential')
