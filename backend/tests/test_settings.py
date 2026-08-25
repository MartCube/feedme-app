"""GET / PUT /settings — appearance preferences that follow the account, not the browser."""

from typing import get_args

from django.test import Client

from core.api.settings import SettingsSchema
from core.auth import issue_token
from core.models import UserSettings

DEFAULTS = {'theme': 'ink', 'feed_list_style': 'list', 'scrollbar_style': 'thin'}
CHANGED = {'theme': 'claude', 'feed_list_style': 'cards', 'scrollbar_style': 'auto'}


def put_settings(client, payload):
    return client.put('/api/v1/settings', payload, content_type='application/json')


def test_settings_401s_without_a_token(client):
    assert client.get('/api/v1/settings').status_code == 401


def test_settings_reads_as_the_defaults_before_anything_is_saved(authed_client):
    response = authed_client.get('/api/v1/settings')

    assert response.status_code == 200
    assert response.json() == DEFAULTS


def test_reading_settings_creates_no_row(authed_client, user):
    """A read must not cause a write — the row appears on the first PUT, not before."""
    authed_client.get('/api/v1/settings')

    assert not UserSettings.objects.filter(user=user).exists()


def test_settings_survive_a_round_trip(authed_client):
    response = put_settings(authed_client, CHANGED)

    assert response.status_code == 200
    assert response.json() == CHANGED
    assert authed_client.get('/api/v1/settings').json() == CHANGED


def test_a_second_write_updates_the_one_row(authed_client, user):
    put_settings(authed_client, CHANGED)
    put_settings(authed_client, DEFAULTS)

    assert UserSettings.objects.filter(user=user).count() == 1
    assert authed_client.get('/api/v1/settings').json() == DEFAULTS


def test_a_partial_body_is_rejected(authed_client, user):
    """PUT replaces the whole resource, so a missing field is a 422, not a silent default."""
    response = put_settings(authed_client, {'theme': 'claude'})

    assert response.status_code == 422
    assert not UserSettings.objects.filter(user=user).exists()


def test_a_value_outside_the_allowed_set_is_rejected(authed_client):
    response = put_settings(authed_client, {**CHANGED, 'theme': 'solarized'})

    assert response.status_code == 422


def test_the_schemas_literals_match_the_models_choices():
    """The two lists are written out separately; this is what stops them drifting."""
    fields = SettingsSchema.model_fields

    assert set(get_args(fields['theme'].annotation)) == set(UserSettings.Theme.values)
    assert set(get_args(fields['feed_list_style'].annotation)) == set(
        UserSettings.FeedListStyle.values
    )
    assert set(get_args(fields['scrollbar_style'].annotation)) == set(
        UserSettings.ScrollbarStyle.values
    )


def test_settings_are_per_account(authed_client, other_user):
    put_settings(authed_client, CHANGED)

    theirs = Client(headers={'authorization': f'Bearer {issue_token(other_user)}'})

    assert theirs.get('/api/v1/settings').json() == DEFAULTS
