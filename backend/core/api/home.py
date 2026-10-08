"""The home screen in one round-trip, and the write that reorders it.

Every app launch waits on GET /home, so it answers in a fixed number of queries no matter
how many feeds the account has: the feeds, then every member with its source, prefetched.

A feed is a user's named group of sources — one or many (docs/data-model.md § Feed). The home
list is the feeds in order; there is nothing nested to interleave, so the order is one column.
"""

from collections import Counter
from typing import Literal

from django.db import transaction
from django.db.models import Count, Max, Prefetch
from ninja import Router, Schema, Status
from ninja.errors import HttpError

from .. import images
from ..models import Feed, FeedSource, SavedPost
from .errors import ErrorSchema

router = Router(tags=['home'])

SourceType = Literal['website', 'youtube', 'reddit']


class FeedSourceSchema(Schema):
    """One source inside one feed. `name` is what the app shows — the user's rename in this
    feed, or the source's own title when there is none; `title` is always the source's own,
    so a rename form can offer it back."""

    uid: str
    name: str
    title: str
    # a Literal, not a str: the OpenAPI schema then carries the three values, so the
    # generated TypeScript keeps the FeedType union
    type: SourceType
    site_url: str
    feed_url: str
    # a signed proxy URL, or null — the app renders initials then (docs/images.md)
    icon: str | None
    enabled: bool


class HomeFeedSchema(Schema):
    uid: str
    name: str
    description: str
    # in the feed's own order
    sources: list[FeedSourceSchema]


class SavedCountsSchema(Schema):
    bookmarks: int
    favorites: int
    later: int


class HomeSchema(Schema):
    # in display order
    feeds: list[HomeFeedSchema]
    saved_counts: SavedCountsSchema


class HomeOrderSchema(Schema):
    uids: list[str]


@router.get('/home', response={200: HomeSchema, 401: ErrorSchema}, operation_id='get_home')
def home(request):
    user = request.auth
    return {
        'feeds': [feed_payload(feed) for feed in with_members(Feed.objects.filter(user=user))],
        'saved_counts': _saved_counts(user),
    }


@router.put(
    '/home/order',
    response={204: None, 401: ErrorSchema, 422: ErrorSchema},
    operation_id='set_home_order',
)
def set_home_order(request, payload: HomeOrderSchema):
    user = request.auth

    # Read, validate and write inside one transaction, with the caller's rows locked: two
    # devices reordering at once are serialised, and a feed created in between fails the
    # validation loudly (a uid missing from the order) instead of a stale sequence landing.
    with transaction.atomic():
        feeds = {feed.uid: feed for feed in Feed.objects.filter(user=user).select_for_update()}
        _validate_order(payload.uids, set(feeds))
        for position, uid in enumerate(payload.uids):
            feeds[uid].order = position
        Feed.objects.bulk_update(feeds.values(), ['order'])

    return Status(204, None)


def with_members(feeds):
    """Feeds with their members and each member's source, in two extra queries total."""
    return feeds.prefetch_related(
        Prefetch('members', queryset=FeedSource.objects.select_related('source').order_by('order'))
    )


def feed_payload(feed):
    """A feed as HomeFeedSchema reads it. Shared by /home and every feed write, so a write
    answers with exactly the shape the home list holds and the store can swap it in."""
    return {
        'uid': feed.uid,
        'name': feed.name,
        'description': feed.description,
        'sources': [
            {
                'uid': member.source.uid,
                'name': member.name or member.source.title or member.source.feed_url,
                'title': member.source.title,
                'type': member.source.type,
                'site_url': member.source.site_url,
                'feed_url': member.source.feed_url,
                'icon': images.icon(member.source.icon_url),
                'enabled': member.enabled,
            }
            for member in feed.members.all()
        ],
    }


def clean_name(name):
    """A user's own name for a feed or a source, as the column will take it — or a 422.

    The NUL check is not pedantry: Postgres refuses the byte in any text column, and without
    this the save is a 500 rather than a validation error.
    """
    cleaned = name.strip()
    if not cleaned:
        raise HttpError(422, 'name cannot be empty')
    if '\x00' in cleaned:
        raise HttpError(422, 'name cannot contain control characters')
    return cleaned


def next_feed_order(user):
    """One past the end of the home list, for a feed joining it."""
    highest = Feed.objects.filter(user=user).aggregate(Max('order'))['order__max']
    return 0 if highest is None else highest + 1


def _saved_counts(user):
    counts = dict(SavedPost.objects.filter(user=user).values_list('group').annotate(Count('id')))
    return {group: counts.get(group, 0) for group in SavedPost.Group.values}


def _validate_order(uids, owned):
    """The payload has to be exactly today's feeds — no more, no less.

    Half-applying a stale order is worse than refusing it: the client is holding a view of
    the list that no longer exists (a feed added on another device, say), and the fix is to
    re-read /home.
    """
    duplicates = sorted(uid for uid, seen in Counter(uids).items() if seen > 1)
    if duplicates:
        raise HttpError(422, f'duplicate uids: {", ".join(duplicates)}')

    unknown = sorted(set(uids) - owned)
    if unknown:
        raise HttpError(422, f'unknown uid: {", ".join(unknown)}')

    missing = sorted(owned - set(uids))
    if missing:
        raise HttpError(422, f'missing from the order: {", ".join(missing)}')
