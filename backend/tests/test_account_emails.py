"""The two account emails — confirm your address, reset your password — and the endpoints
their links land on.

Sending is the worker's job (core/tasks.py `send_account_email`), so the endpoint tests check
what gets enqueued, and the email tests call the actor's function directly. Links are read
back out of Django's test outbox, exactly as a person would click them.
"""

import re
from datetime import timedelta
from unittest import mock

import pytest
from django.core import mail
from django.core.cache import cache
from dramatiq import Message

from core import emails, tasks
from core.api import account
from core.auth import issue_token
from core.models import AuthToken, User

SIGNUP = '/api/v1/auth/signup'
FORGOT = '/api/v1/auth/password/forgot'
RESET = '/api/v1/auth/password/reset'
CONFIRM = '/api/v1/auth/email/confirm'
RESEND = '/api/v1/auth/email/resend'
PASSWORD = 'quiet-reading-list'
NEW_PASSWORD = 'louder-reading-list'


def post(client, url, body=None, **headers):
    return client.post(url, body or {}, content_type='application/json', headers=headers)


def queued(broker):
    """(user pk, kind) of every account email waiting for the worker."""
    queue = broker.queues[tasks.send_account_email.queue_name]
    return [tuple(Message.decode(data).args) for data in list(queue.queue)]


def token_from(message):
    return re.search(r'\?token=(\S+)', message.body).group(1)


@pytest.fixture
def password_user(db):
    return User.objects.create_user(email='reader@example.com', password=PASSWORD)


@pytest.fixture
def send_now(stub_broker):
    """Run whatever the request enqueued, as the worker would, and hand back the outbox."""

    def _run():
        for pk, kind in queued(stub_broker):
            tasks.send_account_email.fn(pk, kind)
        stub_broker.flush_all()
        return mail.outbox

    return _run


# --- sign-up sends a confirmation ------------------------------------------------------


def test_sign_up_queues_a_confirmation_email(
    db, client, stub_broker, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        response = post(client, SIGNUP, {'email': 'reader@example.com', 'password': PASSWORD})

    assert response.status_code == 200
    user = User.objects.get()
    assert not user.email_verified
    assert queued(stub_broker) == [(user.pk, 'confirm')]


def test_me_reports_whether_the_address_is_confirmed(password_user, client):
    token = issue_token(password_user)
    assert (
        client.get('/api/v1/me', headers={'authorization': f'Bearer {token}'}).json()[
            'email_verified'
        ]
        is False
    )

    password_user.email_verified = True
    password_user.save()
    assert (
        client.get('/api/v1/me', headers={'authorization': f'Bearer {token}'}).json()[
            'email_verified'
        ]
        is True
    )


def test_a_google_account_reads_as_confirmed_without_the_column(user, authed_client):
    # linked before the column existed: email_verified is False on the row
    user.google_sub = 'google-sub-1'
    user.save()
    assert authed_client.get('/api/v1/me').json()['email_verified'] is True


# --- confirming --------------------------------------------------------------------------


def test_the_confirmation_link_confirms_without_a_session(password_user, client, send_now):
    tasks.send_account_email.fn(password_user.pk, 'confirm')
    [message] = mail.outbox
    assert message.to == ['reader@example.com']
    assert 'http://localhost:3000/verify-email?token=' in message.body
    # the HTML part carries the same link
    assert token_from(message) in message.alternatives[0][0]

    response = post(client, CONFIRM, {'token': token_from(message)})

    assert response.status_code == 204
    password_user.refresh_from_db()
    assert password_user.email_verified


def test_a_confirmation_link_is_spent_once_used(password_user, client):
    token = emails.make_token(password_user, 'confirm')
    assert post(client, CONFIRM, {'token': token}).status_code == 204
    assert post(client, CONFIRM, {'token': token}).status_code == 400


def test_a_confirmation_link_expires_after_three_days(password_user, client):
    token = emails.make_token(password_user, 'confirm')
    later = emails._ConfirmTokens._now(emails.KINDS['confirm'].tokens) + timedelta(days=3, hours=1)
    with mock.patch.object(emails._ConfirmTokens, '_now', return_value=later):
        assert post(client, CONFIRM, {'token': token}).status_code == 400


@pytest.mark.parametrize('token', ['', 'garbage', 'MQ.not-a-proof', '.', 'Zm9v.1-2'])
def test_a_malformed_token_is_one_plain_refusal(password_user, client, token):
    response = post(client, CONFIRM, {'token': token})
    assert response.status_code == 400
    assert 'expired' in response.json()['detail']


def test_a_reset_token_does_not_confirm_and_vice_versa(password_user, client):
    reset = emails.make_token(password_user, 'reset')
    confirm = emails.make_token(password_user, 'confirm')
    assert post(client, CONFIRM, {'token': reset}).status_code == 400
    assert post(client, RESET, {'token': confirm, 'password': NEW_PASSWORD}).status_code == 400


def test_resend_queues_another_confirmation(
    password_user, client, stub_broker, django_capture_on_commit_callbacks
):
    token = issue_token(password_user)
    with django_capture_on_commit_callbacks(execute=True):
        response = post(client, RESEND, authorization=f'Bearer {token}')

    assert response.status_code == 204
    assert queued(stub_broker) == [(password_user.pk, 'confirm')]


def test_resend_does_nothing_for_a_confirmed_address(
    password_user, client, stub_broker, django_capture_on_commit_callbacks
):
    password_user.email_verified = True
    password_user.save()
    with django_capture_on_commit_callbacks(execute=True):
        response = post(client, RESEND, authorization=f'Bearer {issue_token(password_user)}')

    assert response.status_code == 204
    assert queued(stub_broker) == []


def test_resend_needs_a_session(db, client):
    assert post(client, RESEND).status_code == 401


def test_a_second_email_inside_the_cooldown_is_skipped(password_user):
    tasks.send_account_email.fn(password_user.pk, 'confirm')
    tasks.send_account_email.fn(password_user.pk, 'confirm')
    assert len(mail.outbox) == 1

    cache.clear()  # the minute has passed
    tasks.send_account_email.fn(password_user.pk, 'confirm')
    assert len(mail.outbox) == 2


def test_a_failed_send_releases_the_cooldown_for_the_retry(password_user):
    with mock.patch('django.core.mail.EmailMultiAlternatives.send', side_effect=OSError('down')):
        with pytest.raises(OSError):
            tasks.send_account_email.fn(password_user.pk, 'reset')

    tasks.send_account_email.fn(password_user.pk, 'reset')
    assert len(mail.outbox) == 1


def test_the_worker_skips_a_deleted_account_and_a_confirmed_address(password_user):
    pk = password_user.pk
    password_user.email_verified = True
    password_user.save()
    tasks.send_account_email.fn(pk, 'confirm')

    password_user.delete()
    tasks.send_account_email.fn(pk, 'reset')

    assert mail.outbox == []


# --- forgot + reset ----------------------------------------------------------------------


def test_forgot_answers_the_same_for_an_unknown_address(
    db, client, stub_broker, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        response = post(client, FORGOT, {'email': 'nobody@example.com'})

    assert response.status_code == 204
    assert queued(stub_broker) == []


def test_forgot_then_reset_signs_in_with_the_new_password_and_ends_old_sessions(
    password_user, client, send_now, django_capture_on_commit_callbacks
):
    old_session = issue_token(password_user)
    with django_capture_on_commit_callbacks(execute=True):
        assert post(client, FORGOT, {'email': ' Reader@Example.com '}).status_code == 204
    [message] = send_now()
    assert '/reset-password?token=' in message.body

    response = post(client, RESET, {'token': token_from(message), 'password': NEW_PASSWORD})

    assert response.status_code == 200
    password_user.refresh_from_db()
    assert password_user.check_password(NEW_PASSWORD)
    # the inbox was proved, so the address is confirmed too
    assert password_user.email_verified
    # only the session the reset just opened survives
    assert AuthToken.objects.filter(user=password_user).count() == 1
    me = client.get('/api/v1/me', headers={'authorization': f'Bearer {old_session}'})
    assert me.status_code == 401
    new = client.get('/api/v1/me', headers={'authorization': f'Bearer {response.json()["token"]}'})
    assert new.status_code == 200


def test_a_reset_link_works_once(password_user, client):
    token = emails.make_token(password_user, 'reset')
    assert post(client, RESET, {'token': token, 'password': NEW_PASSWORD}).status_code == 200
    assert (
        post(client, RESET, {'token': token, 'password': 'another-reading-list'}).status_code == 400
    )


def test_a_reset_link_expires_after_an_hour(password_user, client):
    token = emails.make_token(password_user, 'reset')
    later = emails._ResetTokens._now(emails.KINDS['reset'].tokens) + timedelta(minutes=61)
    with mock.patch.object(emails._ResetTokens, '_now', return_value=later):
        response = post(client, RESET, {'token': token, 'password': NEW_PASSWORD})
    assert response.status_code == 400


def test_a_reset_refuses_a_weak_password_and_keeps_the_link_usable(password_user, client):
    token = emails.make_token(password_user, 'reset')
    response = post(client, RESET, {'token': token, 'password': 'short1'})
    assert response.status_code == 422
    password_user.refresh_from_db()
    assert password_user.check_password(PASSWORD)
    assert post(client, RESET, {'token': token, 'password': NEW_PASSWORD}).status_code == 200


def test_a_google_only_account_can_reset_to_its_first_password(user, client):
    # `user` has no usable password
    token = emails.make_token(user, 'reset')
    assert post(client, RESET, {'token': token, 'password': NEW_PASSWORD}).status_code == 200
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)


# --- what confirmation changes about Google sign-in --------------------------------------


@pytest.fixture
def google_says(monkeypatch):
    def _says(email, sub='google-sub-1'):
        # where account.py looks it up; the library boundary is test_google_signin.py's
        monkeypatch.setattr(
            account, 'verify_google_credential', lambda credential: {'sub': sub, 'email': email}
        )

    return _says


def test_google_keeps_the_password_of_a_confirmed_account(password_user, client, google_says):
    password_user.email_verified = True
    password_user.save()
    session = issue_token(password_user)
    google_says('reader@example.com')

    response = post(client, '/api/v1/auth/google', {'credential': 'x'})

    assert response.status_code == 200
    password_user.refresh_from_db()
    assert password_user.google_sub == 'google-sub-1'
    assert password_user.check_password(PASSWORD)
    assert (
        client.get('/api/v1/me', headers={'authorization': f'Bearer {session}'}).status_code == 200
    )


def test_google_still_takes_over_an_unconfirmed_password_account(
    password_user, client, google_says
):
    google_says('reader@example.com')

    response = post(client, '/api/v1/auth/google', {'credential': 'x'})

    assert response.status_code == 200
    password_user.refresh_from_db()
    assert not password_user.has_usable_password()
    assert password_user.email_verified


def test_a_new_google_account_is_confirmed(db, client, google_says):
    google_says('new@example.com')
    post(client, '/api/v1/auth/google', {'credential': 'x'})
    assert User.objects.get().email_verified
