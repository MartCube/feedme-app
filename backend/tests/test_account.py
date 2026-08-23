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
