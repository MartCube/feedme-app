"""Feeds and the sources inside them: create, edit, delete.

The read side of a feed lives in posts.py; this is the writes behind the add wizard and the
feed page. A feed is the user's named group of sources (docs/data-model.md § Feed); every
write here answers with the whole feed in HomeFeedSchema's shape, so the app swaps one row of
its home list rather than re-reading /home.

The awkward part is that a `Source` is global and a feed is yours. Adding one has to
find-or-create the shared row, and removing the last link to it has to leave it behind for the
next person — deactivated, so polling stops, but not deleted, so coming back costs nothing.
"""

from django.db import IntegrityError, transaction
from django.utils import timezone
from ninja import Field, Router, Schema, Status
from ninja.errors import HttpError
from pydantic import HttpUrl, field_validator

# infer_type lives with discovery, which knows every other way to name a source; this
# module only ever sees a URL, and re-exporting keeps it importable from where it is used.
from ..discover import infer_type
from ..ingest import ERROR, POLL_INTERVAL, ingest_source
from ..models import Feed, FeedSource, Source
from .errors import ErrorSchema
from .home import HomeFeedSchema, clean_name, feed_payload, next_feed_order, with_members

router = Router(tags=['feeds'])

FEED_URL_MAX_LENGTH = Source._meta.get_field('feed_url').max_length
DESCRIPTION_MAX_LENGTH = 1000


def _fits_the_column(url):
    # pydantic's own ceiling is 2083; the column's is 500. Refusing beats slicing — a
    # truncated URL is a *different* URL, fetched and then reported as "not a feed".
    if url is not None and len(str(url)) > FEED_URL_MAX_LENGTH:
        raise ValueError(f'must be at most {FEED_URL_MAX_LENGTH} characters')
    return url


class CreateFeedSchema(Schema):
    # blank is allowed only with a feed_url: the source's own title fills it then
    name: str = Field(default='', max_length=300)
    # blank → the first source's own description, when there is one
    description: str = Field(default='', max_length=DESCRIPTION_MAX_LENGTH)
    # the add wizard's "New feed": the feed and its first source in one call, so a URL that
    # turns out not to be a feed leaves no empty feed behind
    feed_url: HttpUrl | None = None

    _fits = field_validator('feed_url')(_fits_the_column)


class UpdateFeedSchema(Schema):
    """Every field optional — omitted means "leave it alone"."""

    name: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)


class AddSourceSchema(Schema):
    # HttpUrl, not str: pydantic rejects what isn't a URL before any of this runs, so the
    # 422 for a typo costs no network call. Discovery results carry this same field.
    feed_url: HttpUrl

    _fits = field_validator('feed_url')(_fits_the_column)


class UpdateSourceSchema(Schema):
    """Every field optional. `name: ""` drops the rename back to the source's own title;
    a new `feed_url` swaps the source behind this row for another."""

    name: str | None = Field(default=None, max_length=300)
    enabled: bool | None = None
    feed_url: HttpUrl | None = None

    _fits = field_validator('feed_url')(_fits_the_column)


@router.post(
    '/feeds',
    response={201: HomeFeedSchema, 401: ErrorSchema, 422: ErrorSchema},
    operation_id='create_feed',
)
def create_feed(request, payload: CreateFeedSchema):
    user = request.auth
    # resolved before the transaction: it may fetch, and a network call has no business
    # holding a database lock open
    source = resolve_source(str(payload.feed_url)) if payload.feed_url else None
    if source is None and not payload.name.strip():
        raise HttpError(422, 'name cannot be empty')

    with transaction.atomic():
        feed = Feed.objects.create(
            user=user,
            name=clean_name(payload.name) if payload.name.strip() else _source_name(source),
            description=_clean_description(payload.description)
            or (source.description if source else ''),
            order=next_feed_order(user),
        )
        if source:
            FeedSource.objects.create(feed=feed, source=source)

    return Status(201, _reread(feed))


@router.patch(
    '/feeds/{uid}',
    response={200: HomeFeedSchema, 401: ErrorSchema, 404: ErrorSchema, 422: ErrorSchema},
    operation_id='update_feed',
)
def update_feed(request, uid: str, payload: UpdateFeedSchema):
    feed = own_feed(request.auth, uid)
    if payload.name is not None:
        feed.name = clean_name(payload.name)
    if payload.description is not None:
        feed.description = _clean_description(payload.description)
    feed.save(update_fields=['name', 'description'])
    return _reread(feed)


@router.delete(
    '/feeds/{uid}',
    response={204: None, 401: ErrorSchema, 404: ErrorSchema},
    operation_id='delete_feed',
)
def delete_feed(request, uid: str):
    feed = own_feed(request.auth, uid)
    # read before the delete, while the members still point at them
    sources = list(feed.sources.all())
    with transaction.atomic():
        # FeedSource.feed is CASCADE, so every member goes with it
        feed.delete()
        for source in sources:
            deactivate_if_orphaned(source)
    return Status(204, None)


@router.post(
    '/feeds/{uid}/sources',
    response={201: HomeFeedSchema, 401: ErrorSchema, 404: ErrorSchema, 422: ErrorSchema},
    operation_id='add_source',
)
def add_source(request, uid: str, payload: AddSourceSchema):
    feed = own_feed(request.auth, uid)
    source = resolve_source(str(payload.feed_url))
    try:
        with transaction.atomic():
            FeedSource.objects.create(feed=feed, source=source, order=_next_member_order(feed))
    except IntegrityError:
        # already in this feed — a second tap, or the same source pasted twice;
        # unique_source_per_feed caught it
        raise HttpError(422, 'That source is already in this feed.') from None
    return Status(201, _reread(feed))


@router.patch(
    '/feeds/{uid}/sources/{source_uid}',
    response={200: HomeFeedSchema, 401: ErrorSchema, 404: ErrorSchema, 422: ErrorSchema},
    operation_id='update_source',
)
def update_source(request, uid: str, source_uid: str, payload: UpdateSourceSchema):
    feed = own_feed(request.auth, uid)
    member = _own_member(feed, source_uid)
    fields = []

    if payload.name is not None:
        # empty is allowed here, unlike a feed's name: it means "the source's own title"
        member.name = clean_name(payload.name) if payload.name.strip() else ''
        fields.append('name')
    if payload.enabled is not None:
        member.enabled = payload.enabled
        fields.append('enabled')

    previous = None
    if payload.feed_url is not None and str(payload.feed_url) != member.source.feed_url:
        # The link is the source's identity, and the Source is shared — editing its URL
        # would repoint every other subscriber. Changing the link swaps which source this
        # row holds instead; the rename and the on/off stay with the row.
        replacement = resolve_source(str(payload.feed_url))
        if feed.members.filter(source=replacement).exists():
            raise HttpError(422, 'That source is already in this feed.')
        previous, member.source = member.source, replacement
        fields.append('source')

    with transaction.atomic():
        if fields:
            member.save(update_fields=fields)
        if previous:
            deactivate_if_orphaned(previous)

    return _reread(feed)


@router.delete(
    '/feeds/{uid}/sources/{source_uid}',
    response={200: HomeFeedSchema, 401: ErrorSchema, 404: ErrorSchema},
    operation_id='remove_source',
)
def remove_source(request, uid: str, source_uid: str):
    # A feed may end up with no sources — it stays, empty, until the user adds one or
    # deletes it. Deleting it for them would throw away the name and description they wrote.
    feed = own_feed(request.auth, uid)
    member = _own_member(feed, source_uid)
    source = member.source
    with transaction.atomic():
        member.delete()
        deactivate_if_orphaned(source)
    return _reread(feed)


def resolve_source(feed_url):
    """The shared Source behind a URL — found, revived, or created and fetched — or a 422.

    Fetching is the one place ingest runs inline. The caller is waiting to find out whether
    what they pasted is a feed at all, and fetching it *is* the answer — there's nothing
    cheaper to validate against.
    """
    source, created = Source.objects.get_or_create(
        feed_url=feed_url,
        # next_fetch_at is the same claim the sweep makes before it enqueues (core/tasks.py):
        # the row exists before the inline fetch below does, and a source with no
        # next_fetch_at is due *now* — a sweep firing mid-fetch would poll it again from the
        # worker. Ingest overwrites the claim with the real schedule either way.
        defaults={'type': infer_type(feed_url), 'next_fetch_at': timezone.now() + POLL_INTERVAL},
    )
    if created:
        try:
            failed = ingest_source(source).status == ERROR
        except Exception:
            # ingest_source records what it can; whatever still escapes must not leave a
            # global row that the next attempt would find, skip fetching, and follow
            source.delete()
            raise
        if failed:
            # a typo shouldn't leave a dead global row behind for everyone
            source.delete()
            raise HttpError(422, "That URL isn't a feed.")
        # ingest backfills title / description / site_url / icon_url from the feed itself
        source.refresh_from_db()
    elif not source.active:
        # its last follower left earlier; this one starts the polling again
        source.active = True
        source.next_fetch_at = None
        source.error_count = 0
        source.save(update_fields=['active', 'next_fetch_at', 'error_count'])
    return source


def own_feed(user, uid):
    feed = Feed.objects.filter(user=user, uid=uid).first()
    if feed is None:
        # 404 rather than 403 on someone else's feed: which of the two it is isn't the
        # caller's business, same rule as post detail
        raise HttpError(404, f'no such feed: {uid}')
    return feed


def deactivate_if_orphaned(source):
    """Stop polling a source nobody follows — but keep the row and its posts.

    Deleting it would throw away everything already fetched and every saved post pointing at
    it (FeedSource.source is PROTECT, Post.source is CASCADE). Deactivating costs one boolean
    and makes coming back free.
    """
    if source.active and not source.feeds.exists():
        source.active = False
        source.save(update_fields=['active'])


def _own_member(feed, source_uid):
    member = feed.members.select_related('source').filter(source__uid=source_uid).first()
    if member is None:
        raise HttpError(404, f'no such source in this feed: {source_uid}')
    return member


def _next_member_order(feed):
    last = feed.members.order_by('-order').values_list('order', flat=True).first()
    return 0 if last is None else last + 1


def _source_name(source):
    return source.title or source.feed_url


def _clean_description(description):
    if '\x00' in description:
        raise HttpError(422, 'description cannot contain control characters')
    return description.strip()


def _reread(feed):
    return feed_payload(with_members(Feed.objects.filter(pk=feed.pk)).get())
