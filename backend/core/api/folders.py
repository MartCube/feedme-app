"""Creating, editing and deleting folders.

Tagged `home` rather than `feeds`: a folder is home-screen structure. It is read only through
GET /home, ordered by PUT /home/order, and has no stream of its own that isn't the merged read
of its members.

Two rules the database can't express live here. Membership has no constraint that the folder
and the feed share an owner, so every uid the caller sends has to be checked against their own
feeds. And deleting a folder unsubscribes its members *except* those that belong to another
folder (docs/data-model.md § Cascade rules) — a cascade with a condition, which is API logic.
"""

from django.db import transaction
from ninja import Field, Router, Schema, Status
from ninja.errors import HttpError

from ..models import Feed, FolderMember, Source
from .errors import ErrorSchema
from .feeds import deactivate_if_orphaned
from .home import HomeFolderSchema, next_top_level_order

router = Router(tags=['home'])


class CreateFolderSchema(Schema):
    name: str = Field(max_length=300)
    # ordered: position in the list is the member's position in the folder
    feed_uids: list[str] = []


class UpdateFolderSchema(Schema):
    """Every field optional — the folder panel commits a rename and the mutes together, and
    removing a member is a `feed_uids` write. Omitted means "leave it alone", which is what
    separates PATCH here from the full-replace PUT on /settings."""

    name: str | None = Field(default=None, max_length=300)
    feed_uids: list[str] | None = None
    muted_feed_uids: list[str] | None = None


class FolderDeletedSchema(Schema):
    # what the confirm sheet predicted, now counted for real
    unsubscribed_count: int


@router.post(
    '/folders',
    response={201: HomeFolderSchema, 401: ErrorSchema, 422: ErrorSchema},
    operation_id='create_folder',
)
def create_folder(request, payload: CreateFolderSchema):
    user = request.auth
    name = _clean_name(payload.name)

    with transaction.atomic():
        folder = user.folders.create(name=name, order=next_top_level_order(user))
        _set_members(folder, payload.feed_uids, muted_uids=[])

    return Status(201, _payload(folder))


@router.patch(
    '/folders/{uid}',
    response={200: HomeFolderSchema, 401: ErrorSchema, 404: ErrorSchema, 422: ErrorSchema},
    operation_id='update_folder',
)
def update_folder(request, uid: str, payload: UpdateFolderSchema):
    folder = _own_folder(request.auth, uid)
    members = list(folder.members.select_related('feed').order_by('order'))

    if payload.name is not None:
        folder.name = _clean_name(payload.name)
        folder.save(update_fields=['name'])

    if payload.feed_uids is None and payload.muted_feed_uids is None:
        return _payload(folder)

    # Mutes are validated against the membership this call *ends* with, not the one it
    # started from — the panel can mute a feed and drop another in the same Save.
    feed_uids = payload.feed_uids
    if feed_uids is None:
        feed_uids = [member.feed.uid for member in members]
    muted_uids = payload.muted_feed_uids
    if muted_uids is None:
        # Carried over, but only for members that survive this call: removing a feed from a
        # folder drops its mute with it (docs/data-model.md § Cascade rules). A mute the
        # caller sends *explicitly* for a non-member is still a 422 — that's incoherent,
        # not a leftover.
        surviving = set(feed_uids)
        muted_uids = [
            member.feed.uid for member in members if member.muted and member.feed.uid in surviving
        ]

    with transaction.atomic():
        _set_members(folder, feed_uids, muted_uids)

    return _payload(folder)


@router.delete(
    '/folders/{uid}',
    response={200: FolderDeletedSchema, 401: ErrorSchema, 404: ErrorSchema},
    operation_id='delete_folder',
)
def delete_folder(request, uid: str):
    folder = _own_folder(request.auth, uid)

    member_ids = list(folder.members.values_list('feed_id', flat=True))
    # Two plain queries rather than one annotated count: filtering on a multi-valued relation
    # and aggregating over it in the same queryset counts the *filtered* join rows, not the
    # feed's memberships — the same join-reuse trap T5's post list documents.
    elsewhere = set(
        FolderMember.objects.filter(feed_id__in=member_ids)
        .exclude(folder=folder)
        .values_list('feed_id', flat=True)
    )
    orphan_ids = [feed_id for feed_id in member_ids if feed_id not in elsewhere]
    # read before the delete, while the feeds still point at them
    sources = list(Source.objects.filter(feeds__id__in=orphan_ids).distinct())

    with transaction.atomic():
        Feed.objects.filter(id__in=orphan_ids).delete()
        folder.delete()
        for source in sources:
            deactivate_if_orphaned(source)

    return {'unsubscribed_count': len(orphan_ids)}


def _own_folder(user, uid):
    folder = user.folders.filter(uid=uid).first()
    if folder is None:
        raise HttpError(404, f'no such folder: {uid}')
    return folder


def _clean_name(name):
    cleaned = name.strip()
    if not cleaned:
        raise HttpError(422, 'name cannot be empty')
    return cleaned


def _set_members(folder, feed_uids, muted_uids):
    """Replace the folder's membership with exactly `feed_uids`, in that order.

    Feeds dropped out of the folder stay subscribed — they go loose unless another folder
    still holds them, and a loose feed needs a real position in the top-level order (T4 left
    them arriving with a stale 0).
    """
    duplicates = sorted({uid for uid in feed_uids if feed_uids.count(uid) > 1})
    if duplicates:
        raise HttpError(422, f'duplicate feed uids: {", ".join(duplicates)}')

    feeds = {
        feed.uid: feed for feed in Feed.objects.filter(user=folder.user, uid__in=set(feed_uids))
    }
    unknown = sorted(set(feed_uids) - set(feeds))
    if unknown:
        # covers both "no such feed" and "someone else's feed" — the caller learns no more
        # about another account than that this uid isn't theirs
        raise HttpError(422, f'not your feed: {", ".join(unknown)}')

    stray_mutes = sorted(set(muted_uids) - set(feed_uids))
    if stray_mutes:
        raise HttpError(422, f'not in this folder: {", ".join(stray_mutes)}')

    previous = set(folder.members.values_list('feed__uid', flat=True))
    removed = previous - set(feed_uids)

    folder.members.filter(feed__uid__in=removed).delete()
    for position, uid in enumerate(feed_uids):
        FolderMember.objects.update_or_create(
            folder=folder,
            feed=feeds[uid],
            defaults={'order': position, 'muted': uid in set(muted_uids)},
        )

    _rehome_freed_feeds(folder.user, removed)


def _rehome_freed_feeds(user, removed_uids):
    """Give a feed that just went loose a position at the end of the top-level list."""
    if not removed_uids:
        return
    still_nested = set(
        FolderMember.objects.filter(feed__uid__in=removed_uids).values_list('feed__uid', flat=True)
    )
    loose = Feed.objects.filter(user=user, uid__in=removed_uids - still_nested)

    position = next_top_level_order(user)
    freed = []
    for feed in loose:
        feed.order = position
        position += 1
        freed.append(feed)
    Feed.objects.bulk_update(freed, ['order'])


def _payload(folder):
    members = list(folder.members.select_related('feed').order_by('order'))
    return {
        'uid': folder.uid,
        'name': folder.name,
        'feed_uids': [member.feed.uid for member in members],
        'muted_feed_uids': [member.feed.uid for member in members if member.muted],
    }
