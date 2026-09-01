"""Subscribing, renaming and unsubscribing.

The read side of a feed lives in posts.py; this is the writes behind the add wizard and the
edit drawer. Both modules sit under the `feeds` tag — from the app's side it is all one thing:
what you follow.

The awkward part is that a `Source` is global and a `Feed` is yours. Subscribing has to
find-or-create the shared row, and unsubscribing has to leave it behind for the next person —
deactivated, so polling stops, but not deleted, so re-subscribing costs nothing.
"""

from urllib.parse import urlparse

from django.db import transaction
from ninja import Field, Router, Schema, Status
from ninja.errors import HttpError
from pydantic import HttpUrl

from ..ingest import ERROR, ingest_source
from ..models import Feed, Folder, FolderMember, Source
from .errors import ErrorSchema
from .home import HomeFeedSchema, next_top_level_order

router = Router(tags=['feeds'])


class SubscribeSchema(Schema):
    # HttpUrl, not str: pydantic rejects what isn't a URL before any of this runs, so the
    # 422 for a typo costs no network call. T11's discovery results carry this same field.
    feed_url: HttpUrl
    # omitted → the feed lands at the top level
    folder_uid: str | None = None


class RenameFeedSchema(Schema):
    # the model's own limit; pydantic answers 422 rather than the database truncating
    name: str = Field(max_length=300)


@router.post(
    '/feeds',
    response={201: HomeFeedSchema, 401: ErrorSchema, 404: ErrorSchema, 422: ErrorSchema},
    operation_id='subscribe',
)
def subscribe(request, payload: SubscribeSchema):
    user = request.auth
    feed_url = str(payload.feed_url)[: Source._meta.get_field('feed_url').max_length]

    folder = None
    if payload.folder_uid:
        folder = Folder.objects.filter(user=user, uid=payload.folder_uid).first()
        if folder is None:
            raise HttpError(404, f'no such folder: {payload.folder_uid}')

    source, created = Source.objects.get_or_create(
        feed_url=feed_url, defaults={'type': infer_type(feed_url)}
    )
    if not created and Feed.objects.filter(user=user, source=source).exists():
        raise HttpError(422, 'You already follow that feed.')

    if created:
        # The one place ingest runs inline. The caller is waiting to find out whether what
        # they pasted is a feed at all, and fetching it *is* the answer — there's nothing
        # cheaper to validate against. Deliberately outside the transaction below: a network
        # call has no business holding a database lock open.
        if ingest_source(source).status == ERROR:
            # a typo shouldn't leave a dead global row behind for everyone
            source.delete()
            raise HttpError(422, "That URL isn't a feed.")
        # ingest backfills title / site_url / icon_url from the feed itself
        source.refresh_from_db()
    elif not source.active:
        # its last subscriber left earlier; this one starts the polling again
        source.active = True
        source.next_fetch_at = None
        source.error_count = 0
        source.save(update_fields=['active', 'next_fetch_at', 'error_count'])

    with transaction.atomic():
        feed = Feed.objects.create(
            user=user,
            source=source,
            # the user's own name for it, seeded from the feed's title — renameable after
            name=source.title or urlparse(feed_url).hostname or feed_url,
            order=next_top_level_order(user),
        )
        if folder:
            FolderMember.objects.create(folder=folder, feed=feed, order=next_member_order(folder))

    return Status(201, feed)


@router.patch(
    '/feeds/{uid}',
    response={200: HomeFeedSchema, 401: ErrorSchema, 404: ErrorSchema, 422: ErrorSchema},
    operation_id='rename_feed',
)
def rename_feed(request, uid: str, payload: RenameFeedSchema):
    # Name only. feed_url lives on the shared Source — editing it here would repoint every
    # other subscriber's feed (backend-roadmap.md § Contract resolutions, 3).
    feed = own_feed(request.auth, uid)
    name = payload.name.strip()
    if not name:
        raise HttpError(422, 'name cannot be empty')
    feed.name = name
    feed.save(update_fields=['name'])
    return feed


@router.delete(
    '/feeds/{uid}',
    response={204: None, 401: ErrorSchema, 404: ErrorSchema},
    operation_id='unsubscribe',
)
def unsubscribe(request, uid: str):
    feed = own_feed(request.auth, uid)
    source = feed.source
    with transaction.atomic():
        # FolderMember.feed is on_delete=CASCADE, so every membership goes with it
        feed.delete()
        deactivate_if_orphaned(source)
    return Status(204, None)


def own_feed(user, uid):
    feed = Feed.objects.filter(user=user, uid=uid).select_related('source').first()
    if feed is None:
        # 404 rather than 403 on someone else's feed: which of the two it is isn't the
        # caller's business, same rule as post detail
        raise HttpError(404, f'no such feed: {uid}')
    return feed


def deactivate_if_orphaned(source):
    """Stop polling a source nobody follows — but keep the row and its posts.

    Deleting it would throw away everything already fetched and every saved post pointing at
    it (Feed.source is PROTECT, Post.source is CASCADE). Deactivating costs one boolean and
    makes re-subscribing free.
    """
    if source.active and not source.feeds.exists():
        source.active = False
        source.save(update_fields=['active'])


def infer_type(feed_url):
    """Which of the three source types a URL is, by host.

    Inferred here rather than taken from the request: the add wizard's type step is a UI
    filter, and a client is free to be wrong about it. T11's discovery knows more (it
    resolves handles and subreddit names), but a pasted feed URL only has its host to go on.
    """
    host = (urlparse(feed_url).hostname or '').lower()
    for domain, source_type in (
        ('youtube.com', Source.Type.YOUTUBE),
        ('reddit.com', Source.Type.REDDIT),
    ):
        if host == domain or host.endswith(f'.{domain}'):
            return source_type
    return Source.Type.WEBSITE


def next_member_order(folder):
    last = folder.members.order_by('-order').values_list('order', flat=True).first()
    return 0 if last is None else last + 1
