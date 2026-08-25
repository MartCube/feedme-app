"""Admin is the ops UI for sources (docs/backend.md § Fetching pipeline), so the one
piece of it with behaviour — the reset action — is pinned here."""

from datetime import timedelta

from django.utils import timezone

from core.models import Source


def test_the_source_changelist_renders(admin_client, db):
    Source.objects.create(
        type=Source.Type.WEBSITE, feed_url='https://example.com/rss', title='Example'
    )

    response = admin_client.get('/admin/core/source/')

    assert response.status_code == 200
    body = response.content.decode()
    assert 'Example' in body
    assert 'Reset errors and poll on the next run' in body


def test_the_reset_action_revives_a_deactivated_source(admin_client, db):
    source = Source.objects.create(
        type=Source.Type.WEBSITE,
        feed_url='https://example.com/rss',
        active=False,
        error_count=5,
        next_fetch_at=timezone.now() + timedelta(hours=24),
    )

    admin_client.post(
        '/admin/core/source/',
        {'action': 'reset_and_reschedule', '_selected_action': [source.pk]},
        follow=True,
    )

    source.refresh_from_db()
    assert source.active is True
    assert source.error_count == 0
    # cleared, not set to a time — that's what makes it due on the next poll_due
    assert source.next_fetch_at is None
