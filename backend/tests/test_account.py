from django.contrib.auth import get_user_model
from django.test import Client

from core.auth import issue_token
from core.models import AuthToken, Feed, Source


def test_health_needs_no_token(client):
    """The one unguarded endpoint — the compose healthcheck carries no credentials."""
    assert client.get('/api/v1/health').status_code == 200


def test_me_401s_without_a_token(client):
    response = client.get('/api/v1/me')

    assert response.status_code == 401
    assert response.json() == {'detail': 'Unauthorized'}


def test_me_401s_on_a_non_bearer_scheme(client):
    response = client.get('/api/v1/me', headers={'authorization': 'Basic bm90LWEtdG9rZW4='})

    assert response.status_code == 401


def test_me_401s_on_a_bearer_token_that_is_not_ours(db, client):
    """Needs `db`: this is the only 401 case that reaches authenticate() at all —
    the other two short-circuit inside HttpBearer before any query runs."""
    response = client.get('/api/v1/me', headers={'authorization': 'Bearer made-up'})

    assert response.status_code == 401


def test_me_returns_the_signed_in_profile(authed_client, user):
    response = authed_client.get('/api/v1/me')

    assert response.status_code == 200
    body = response.json()
    assert body['email'] == user.email
    assert body['provider'] == 'dev'
    assert body['created_at'].startswith(str(user.created_at.year))


def test_logout_revokes_the_presented_token_immediately(authed_client):
    assert authed_client.post('/api/v1/auth/logout').status_code == 204

    assert authed_client.get('/api/v1/me').status_code == 401


def test_logout_leaves_other_devices_signed_in(authed_client, user):
    other = Client(headers={'authorization': f'Bearer {issue_token(user, device_label="phone")}'})

    assert authed_client.post('/api/v1/auth/logout').status_code == 204

    assert other.get('/api/v1/me').status_code == 200


def test_delete_me_removes_the_account_and_its_data(authed_client, user):
    source = Source.objects.create(type=Source.Type.WEBSITE, feed_url='https://example.com/rss')
    Feed.objects.create(user=user, source=source, name='Example')

    assert authed_client.delete('/api/v1/me').status_code == 204

    assert not get_user_model().objects.filter(pk=user.pk).exists()
    assert not Feed.objects.exists()
    assert not AuthToken.objects.exists()
    # the shared Source outlives the user who subscribed to it
    assert Source.objects.filter(pk=source.pk).exists()
