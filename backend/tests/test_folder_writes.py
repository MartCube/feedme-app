"""POST /folders, PATCH /folders/{uid}, DELETE /folders/{uid}.

Folders are read through GET /home (test_home.py); this is the editing behind the edit
drawer, and the three cascade rules in docs/data-model.md § Cascade rules that go with it.
"""

from core.models import Feed, Folder, FolderMember, Source


def create(client, name='Dev', **body):
    return client.post('/api/v1/folders', {'name': name, **body}, content_type='application/json')


def update(client, uid, **body):
    return client.patch(f'/api/v1/folders/{uid}', body, content_type='application/json')


def test_the_writes_401_without_a_token(client):
    assert create(client).status_code == 401
    assert update(client, 'folder_x', name='Nope').status_code == 401
    assert client.delete('/api/v1/folders/folder_x').status_code == 401


def test_creating_an_empty_folder(authed_client, user):
    body = create(authed_client, name='  Dev  ').json()

    folder = Folder.objects.get(user=user)
    assert body == {
        'uid': folder.uid,
        'name': 'Dev',
        'feed_uids': [],
        'muted_feed_uids': [],
    }


def test_creating_a_folder_with_members_keeps_the_order_given(authed_client, user, make_feed):
    first, second = make_feed(user, name='One'), make_feed(user, name='Two')

    body = create(authed_client, feed_uids=[second.uid, first.uid]).json()

    assert body['feed_uids'] == [second.uid, first.uid]


def test_a_new_folder_lands_at_the_end_of_the_top_level_order(authed_client, user, make_feed):
    make_feed(user, name='Loose', order=3)

    uid = create(authed_client).json()['uid']

    assert Folder.objects.get(uid=uid).order == 4


def test_a_blank_name_422s(authed_client):
    assert create(authed_client, name='   ').status_code == 422
    assert not Folder.objects.exists()


def test_a_name_with_a_nul_byte_422s(authed_client, user, make_folder):
    """Postgres refuses a NUL in any text column — without this it is a 500 on the save."""
    folder = make_folder(user, name='Dev')

    assert create(authed_client, name='a\x00b').status_code == 422
    assert update(authed_client, folder.uid, name='a\x00b').status_code == 422

    folder.refresh_from_db()
    assert folder.name == 'Dev'
    assert Folder.objects.count() == 1


def test_renaming_leaves_the_membership_alone(authed_client, user, make_feed, make_folder):
    feed = make_feed(user)
    folder = make_folder(user, name='Dev', feeds=[feed], muted=[feed])

    body = update(authed_client, folder.uid, name='Development').json()

    folder.refresh_from_db()
    assert folder.name == 'Development'
    assert body['feed_uids'] == [feed.uid]
    assert body['muted_feed_uids'] == [feed.uid]


def test_a_rename_is_not_kept_when_the_membership_in_the_same_call_is_refused(
    authed_client, user, make_feed, make_folder
):
    """The panel commits a rename and the member changes in one Save; a 422 for one half
    must not leave the other half applied, or the screen and the row disagree."""
    feed = make_feed(user)
    folder = make_folder(user, name='Dev', feeds=[feed])

    response = update(authed_client, folder.uid, name='Development', feed_uids=['feed_nope'])

    assert response.status_code == 422
    folder.refresh_from_db()
    assert folder.name == 'Dev'
    assert list(folder.members.values_list('feed', flat=True)) == [feed.pk]


def test_muting_a_member_without_touching_the_membership(
    authed_client, user, make_feed, make_folder
):
    kept, muted = make_feed(user, name='Kept'), make_feed(user, name='Muted')
    folder = make_folder(user, feeds=[kept, muted])

    body = update(authed_client, folder.uid, muted_feed_uids=[muted.uid]).json()

    assert body['feed_uids'] == [kept.uid, muted.uid]
    assert body['muted_feed_uids'] == [muted.uid]


def test_a_rename_and_a_mute_commit_together(authed_client, user, make_feed, make_folder):
    feed = make_feed(user)
    folder = make_folder(user, name='Dev', feeds=[feed])

    body = update(authed_client, folder.uid, name='Reading', muted_feed_uids=[feed.uid]).json()

    assert body['name'] == 'Reading'
    assert body['muted_feed_uids'] == [feed.uid]


def test_muting_a_feed_that_isnt_a_member_422s(authed_client, user, make_feed, make_folder):
    outsider = make_feed(user, name='Outside')
    folder = make_folder(user, feeds=[make_feed(user, name='Inside')])

    response = update(authed_client, folder.uid, muted_feed_uids=[outsider.uid])

    assert response.status_code == 422
    assert not FolderMember.objects.filter(folder=folder, muted=True).exists()


def test_another_users_feed_cannot_be_added_as_a_member(
    authed_client, user, other_user, make_feed, make_folder
):
    theirs = make_feed(other_user, name='Theirs')
    folder = make_folder(user)

    response = update(authed_client, folder.uid, feed_uids=[theirs.uid])

    # FolderMember has no database constraint that the folder and the feed share an owner —
    # this check is the constraint (backend-roadmap.md, the obligations T4 handed to T7)
    assert response.status_code == 422
    assert response.json()['detail'] == f'not your feed: {theirs.uid}'
    assert not FolderMember.objects.filter(folder=folder).exists()


def test_a_repeated_feed_uid_422s(authed_client, user, make_feed, make_folder):
    feed = make_feed(user)
    folder = make_folder(user)

    assert update(authed_client, folder.uid, feed_uids=[feed.uid, feed.uid]).status_code == 422


def test_another_users_folder_is_invisible(authed_client, other_user, make_folder):
    folder = make_folder(other_user, name='Theirs')

    assert update(authed_client, folder.uid, name='Mine').status_code == 404
    assert authed_client.delete(f'/api/v1/folders/{folder.uid}').status_code == 404

    folder.refresh_from_db()
    assert folder.name == 'Theirs'


# --- Cascade rule 1: remove from folder -------------------------------------------------


def test_removing_a_member_keeps_it_subscribed_and_drops_its_mute(
    authed_client, user, make_feed, make_folder
):
    kept, dropped = make_feed(user, name='Kept'), make_feed(user, name='Dropped')
    folder = make_folder(user, feeds=[kept, dropped], muted=[dropped])

    body = update(authed_client, folder.uid, feed_uids=[kept.uid]).json()

    assert body['feed_uids'] == [kept.uid]
    assert body['muted_feed_uids'] == []
    assert Feed.objects.filter(uid=dropped.uid).exists()


def test_a_feed_that_goes_loose_gets_a_fresh_top_level_position(
    authed_client, user, make_feed, make_folder
):
    # order 0 is what a feed created inside a folder carries — the stale value T4 flagged
    nested = make_feed(user, name='Nested', order=0)
    make_feed(user, name='Loose', order=5)
    folder = make_folder(user, feeds=[nested], order=6)

    update(authed_client, folder.uid, feed_uids=[])

    nested.refresh_from_db()
    assert nested.order == 7


def test_a_feed_removed_from_one_folder_stays_nested_in_another(
    authed_client, user, make_feed, make_folder
):
    feed = make_feed(user, order=0)
    keeper = make_folder(user, name='Keeper', feeds=[feed])
    folder = make_folder(user, name='Other', feeds=[feed])

    update(authed_client, folder.uid, feed_uids=[])

    feed.refresh_from_db()
    assert list(keeper.members.values_list('feed__uid', flat=True)) == [feed.uid]
    # still nested, so it keeps the position it had rather than joining the top level
    assert feed.order == 0


# --- Cascade rule 3: delete folder ------------------------------------------------------


def test_deleting_a_folder_unsubscribes_the_members_it_alone_holds(
    authed_client, user, make_feed, make_folder
):
    only_here, also_elsewhere = make_feed(user, name='Only'), make_feed(user, name='Shared')
    make_folder(user, name='Keeper', feeds=[also_elsewhere])
    folder = make_folder(user, name='Doomed', feeds=[only_here, also_elsewhere])

    body = authed_client.delete(f'/api/v1/folders/{folder.uid}').json()

    assert body == {'unsubscribed_count': 1}
    assert not Folder.objects.filter(uid=folder.uid).exists()
    assert not Feed.objects.filter(uid=only_here.uid).exists()
    assert Feed.objects.filter(uid=also_elsewhere.uid).exists()


def test_deleting_a_folder_deactivates_the_sources_it_orphans(
    authed_client, user, other_user, make_feed, make_folder, make_source
):
    lonely, shared = make_source(), make_source()
    make_feed(other_user, source=shared, name='Someone else follows this')
    folder = make_folder(
        user, feeds=[make_feed(user, source=lonely), make_feed(user, source=shared)]
    )

    authed_client.delete(f'/api/v1/folders/{folder.uid}')

    assert not Source.objects.get(pk=lonely.pk).active
    assert Source.objects.get(pk=shared.pk).active


def test_deleting_an_empty_folder_unsubscribes_nothing(authed_client, user, make_folder):
    folder = make_folder(user)

    body = authed_client.delete(f'/api/v1/folders/{folder.uid}').json()

    assert body == {'unsubscribed_count': 0}


def test_a_loose_feed_survives_a_folder_delete_that_never_held_it(
    authed_client, user, make_feed, make_folder
):
    loose = make_feed(user, name='Loose')
    folder = make_folder(user)

    authed_client.delete(f'/api/v1/folders/{folder.uid}')

    assert Feed.objects.filter(uid=loose.uid).exists()
