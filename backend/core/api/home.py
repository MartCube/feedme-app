"""The home screen in one round-trip, and the write that reorders it.

Every app launch waits on GET /home, so it answers in a fixed number of queries no matter
how many feeds the account has — folders and their members are prefetched, loose feeds and
the top-level order are then worked out in memory.

The order itself is the awkward part: the home list interleaves folders and loose feeds,
but those are two tables with two separate `order` columns. PUT /home/order writes one
shared 0..n-1 sequence across both (docs/backend-roadmap.md § Contract resolutions, item 5).
"""

from collections import Counter
from typing import Literal

from django.db import transaction
from django.db.models import Count, Prefetch
from ninja import Field, Router, Schema, Status
from ninja.errors import HttpError

from ..models import Feed, Folder, FolderMember, SavedPost
from .errors import ErrorSchema

router = Router()


class HomeFeedSchema(Schema):
    """A user's handle on a source. `name` is theirs; the rest is the shared Source's,
    flattened in — a Source never surfaces as an entity of its own (backend.md § Vocabulary)."""

    uid: str
    name: str
    # a Literal, not a str: the OpenAPI schema then carries the three values, so the
    # TypeScript T6 generates keeps the FeedType union the frontend already hand-writes
    type: Literal['website', 'youtube', 'reddit'] = Field(alias='source.type')
    site_url: str = Field(alias='source.site_url')
    feed_url: str = Field(alias='source.feed_url')
    icon_url: str = Field(alias='source.icon_url')


class HomeFolderSchema(Schema):
    uid: str
    name: str
    feed_uids: list[str]
    muted_feed_uids: list[str]


class SavedCountsSchema(Schema):
    bookmarks: int
    favorites: int
    later: int


class HomeSchema(Schema):
    folders: list[HomeFolderSchema]
    # every feed, folder members included — membership is expressed by folder.feed_uids,
    # and "loose" is the frontend's own definition: a feed in no folder's list
    feeds: list[HomeFeedSchema]
    # top-level only: folders + loose feeds, in display order
    order: list[str]
    saved_counts: SavedCountsSchema


class HomeOrderSchema(Schema):
    uids: list[str]


@router.get('/home', response={200: HomeSchema, 401: ErrorSchema})
def home(request):
    user = request.auth

    folders = list(
        Folder.objects.filter(user=user).prefetch_related(
            Prefetch(
                'members',
                queryset=FolderMember.objects.select_related('feed').order_by('order'),
            )
        )
    )
    feeds = list(Feed.objects.filter(user=user).select_related('source'))

    member_uids = {member.feed.uid for folder in folders for member in folder.members.all()}
    loose_feeds = [feed for feed in feeds if feed.uid not in member_uids]

    return {
        'folders': [_folder_payload(folder) for folder in folders],
        'feeds': feeds,
        'order': _top_level_order(folders, loose_feeds),
        'saved_counts': _saved_counts(user),
    }


@router.put('/home/order', response={204: None, 401: ErrorSchema, 422: ErrorSchema})
def set_home_order(request, payload: HomeOrderSchema):
    user = request.auth

    folders = {folder.uid: folder for folder in Folder.objects.filter(user=user)}
    feeds = {feed.uid: feed for feed in Feed.objects.filter(user=user)}
    nested = set(FolderMember.objects.filter(folder__user=user).values_list('feed__uid', flat=True))
    top_level = set(folders) | (set(feeds) - nested)

    _validate_order(payload.uids, top_level, nested)

    reordered_folders, reordered_feeds = [], []
    for position, uid in enumerate(payload.uids):
        if uid in folders:
            folders[uid].order = position
            reordered_folders.append(folders[uid])
        else:
            feeds[uid].order = position
            reordered_feeds.append(feeds[uid])

    with transaction.atomic():
        Folder.objects.bulk_update(reordered_folders, ['order'])
        Feed.objects.bulk_update(reordered_feeds, ['order'])

    return Status(204, None)


def _folder_payload(folder):
    members = list(folder.members.all())
    return {
        'uid': folder.uid,
        'name': folder.name,
        'feed_uids': [member.feed.uid for member in members],
        'muted_feed_uids': [member.feed.uid for member in members if member.muted],
    }


def _top_level_order(folders, loose_feeds):
    # Folder.order and Feed.order are separate columns that both default to 0, so a tie
    # across the two tables needs a deterministic break or the list flickers between reads.
    items = sorted([*folders, *loose_feeds], key=lambda item: (item.order, item.uid))
    return [item.uid for item in items]


def _saved_counts(user):
    counts = dict(SavedPost.objects.filter(user=user).values_list('group').annotate(Count('id')))
    return {group: counts.get(group, 0) for group in SavedPost.Group.values}


def _validate_order(uids, top_level, nested):
    """The payload has to be exactly today's top-level list — no more, no less.

    Half-applying a stale order is worse than refusing it: the client is holding a view of
    the list that no longer exists (a feed added on another device, say), and the fix is to
    re-read /home. Saying so out loud also catches a frontend that sends the wrong shape.
    """
    duplicates = sorted(uid for uid, seen in Counter(uids).items() if seen > 1)
    if duplicates:
        raise HttpError(422, f'duplicate uids: {", ".join(duplicates)}')

    # checked before `unknown` so a folder member gets the message that explains itself:
    # its position lives on FolderMember.order, not on Feed.order
    inside_a_folder = sorted(set(uids) & nested)
    if inside_a_folder:
        raise HttpError(422, f'not a top-level uid: {", ".join(inside_a_folder)}')

    unknown = sorted(set(uids) - top_level)
    if unknown:
        raise HttpError(422, f'unknown uid: {", ".join(unknown)}')

    missing = sorted(top_level - set(uids))
    if missing:
        raise HttpError(422, f'missing from the order: {", ".join(missing)}')
