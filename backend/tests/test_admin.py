"""Admin is the ops UI for sources (docs/backend.md § Fetching pipeline) and, until T7's
write endpoints exist, the only way to subscribe a user to a feed. So the two pieces of it
with behaviour are pinned here: the source reset action, and the user page that gathers
everything an account owns."""

from datetime import timedelta

from django.utils import timezone

from core.models import AuthToken, SavedPost, Source, UserSettings


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


def user_page(admin_client, user):
    return admin_client.get(f'/admin/core/user/{user.pk}/change/').content.decode()


def test_the_user_page_gathers_everything_the_account_owns(
    admin_client, user, other_user, make_feed, make_folder
):
    feed = make_feed(user, name='Vue on Medium')
    make_folder(user, name='Dev', feeds=[feed])
    make_feed(other_user, name='Not yours')
    UserSettings.objects.create(user=user, theme=UserSettings.Theme.CLAUDE)

    body = user_page(admin_client, user)

    assert 'Vue on Medium' in body
    assert 'Dev' in body
    assert 'Appearance settings' in body
    # the whole point of the inlines: another account's rows never appear on this page
    assert 'Not yours' not in body


def test_the_user_page_carries_the_saved_pile_and_a_link_to_the_rest(admin_client, user, make_post):
    SavedPost.objects.create(
        user=user, post=make_post(title='Saved thing'), group=SavedPost.Group.LATER
    )

    body = user_page(admin_client, user)

    assert 'Saved thing' in body
    assert f'/admin/core/savedpost/?user__id__exact={user.pk}' in body
    assert '1 saved' in body


def test_the_add_user_form_still_renders(admin_client, db):
    """The saved-posts link is a readonly method, and here it runs against an unsaved
    instance with no pk to count against."""
    assert admin_client.get('/admin/core/user/add/').status_code == 200


def test_the_session_inline_shows_the_device_and_never_the_hash(admin_client, user, auth_token):
    body = user_page(admin_client, user)

    assert 'pytest' in body
    assert AuthToken.objects.get(user=user).token_hash not in body


def test_the_index_lists_only_the_global_tables_and_the_accounts(admin_client, db):
    """Everything a user owns is edited from the user's page, so it has no index entry."""
    body = admin_client.get('/admin/').content.decode()

    for listed in ('/admin/core/user/', '/admin/core/feed/', '/admin/core/source/'):
        assert listed in body
    for hidden in ('/admin/core/folder/', '/admin/core/savedpost/'):
        assert hidden not in body


def test_folder_membership_is_still_editable_on_the_folders_own_page(
    admin_client, user, make_feed, make_folder
):
    """Dropping folders from the index must not cost the mute UI: Django admin has no nested
    inlines, so this page is the only place FolderMember can be edited."""
    folder = make_folder(user, name='Dev', feeds=[make_feed(user)])

    body = admin_client.get(f'/admin/core/folder/{folder.pk}/change/').content.decode()

    assert 'Folder members' in body
    assert 'muted' in body


def test_the_saved_changelist_is_still_reachable_by_url(admin_client, user, make_post):
    """The user page's "N saved" link points here."""
    SavedPost.objects.create(user=user, post=make_post(), group=SavedPost.Group.LATER)

    response = admin_client.get(f'/admin/core/savedpost/?user__id__exact={user.pk}')

    assert response.status_code == 200


def test_settings_are_edited_on_the_user_not_as_a_table_of_their_own(admin_client, db):
    """Unregistered outright, unlike folders and saved posts — nothing links to it."""
    assert admin_client.get('/admin/core/usersettings/').status_code == 404
