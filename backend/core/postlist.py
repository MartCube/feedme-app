"""uid → the posts behind it, and the cursor that pages through them.

`/feeds/{uid}/posts` is one polymorphic operation over five kinds of list, and the order it
tries them in is the frontend's exactly — all → saved → saved_* → feed_*
(`app/utils/feed-title.ts`). Keeping that order in one module per side is what stops the two
from drifting.

Posts are global rows shared by every subscriber, so three of the fields the API returns
depend on who is asking: `source_name` (the caller's own name for the post's source, if they
renamed it), `saved_group` and `saved_at`. They arrive as correlated subqueries — see
`_annotate`.

HttpError is raised from here rather than translated in the API layer: an unknown uid has
exactly one meaning (404) and a private exception type to carry it across one module
boundary would be machinery for nothing. core/search.py resolves scopes by calling
`resolve_stream` directly, so there is one uid order on the server, not two.
"""

import base64
from dataclasses import dataclass
from datetime import datetime

from django.db.models import OuterRef, Q, QuerySet, Subquery
from ninja.errors import HttpError

from .models import Feed, FeedSource, Post, SavedPost

SAVED_PREFIX = 'saved_'


@dataclass(frozen=True)
class Stream:
    """A post list and the field its cursor pages over.

    Saved lists read newest-*saved* first, every other list newest-*published* first, so
    which column orders the stream is part of what resolving a uid decides.
    """

    queryset: QuerySet
    order_field: str


def resolve_stream(user, uid):
    """The posts behind a feed-page uid, in the frontend's resolution order.

    Every branch is rooted in the caller's own rows, so another user's feed uid lands on the
    same 404 as one that never existed.
    """
    if uid == 'all':
        return _stream(user, Q(source__in=_enabled_sources(user)), 'published_at')

    if uid == 'saved':
        return _stream(user, Q(id__in=_saved_post_ids(user)), 'saved_at')

    if uid.startswith(SAVED_PREFIX):
        group = uid.removeprefix(SAVED_PREFIX)
        if group not in SavedPost.Group.values:
            raise HttpError(404, f'no such feed: {uid}')
        return _stream(user, Q(id__in=_saved_post_ids(user, group)), 'saved_at')

    if uid.startswith('feed_'):
        feed = Feed.objects.filter(user=user, uid=uid).first()
        if feed is None:
            raise HttpError(404, f'no such feed: {uid}')
        # a source switched off is filtered here, not on the source: off belongs to *this*
        # feed, so the same source can stay on in another of the user's feeds
        members = FeedSource.objects.filter(feed=feed, enabled=True)
        return _stream(user, Q(source__in=members.values('source_id')), 'published_at')

    raise HttpError(404, f'no such feed: {uid}')


def visible_posts(user):
    """The posts a caller may open and save.

    Posts are global, so "is it mine" is not a user FK — it is this rule: a post from a
    source in any of your feeds (switched on or not), or one you have already saved. The
    second half is what keeps a saved post readable after its source leaves your feeds.
    """
    return _annotate(
        user,
        Post.objects.filter(
            Q(source__in=_followed_sources(user)) | Q(id__in=_saved_post_ids(user))
        ),
    )


def encode_cursor(post, order_field):
    """An opaque marker meaning "everything strictly after this post".

    Not an offset: offsets skip or repeat rows when new posts arrive mid-scroll, which is
    exactly what a feed reader does. It carries the public uid rather than the pk — base64
    is decodable, so a pk inside one is still a pk on the wire.
    """
    return (
        base64.urlsafe_b64encode(f'{getattr(post, order_field).isoformat()}|{post.uid}'.encode())
        .decode()
        .rstrip('=')
    )


def decode_cursor(cursor, order_field):
    """The keyset predicate a cursor stands for, or a 422 if it is not one of ours."""
    try:
        # padding is stripped on the way out to keep the cursor URL-clean
        raw = base64.urlsafe_b64decode(cursor + '=' * (-len(cursor) % 4)).decode()
        value, uid = raw.split('|')
        moment = datetime.fromisoformat(value)
    except ValueError:
        # binascii.Error and UnicodeDecodeError are both ValueError subclasses
        raise HttpError(422, 'invalid cursor') from None
    if moment.tzinfo is None:
        # every cursor we mint carries an offset; one without is hand-built, and Django
        # would otherwise compare it in the default timezone with a warning in the log
        raise HttpError(422, 'invalid cursor')

    # the list is ordered (order_field desc, uid desc), so "after" is a strict tuple compare
    return Q(**{f'{order_field}__lt': moment}) | Q(**{order_field: moment, 'uid__lt': uid})


def page(stream, cursor, limit):
    """One window of a stream, and the cursor that continues it.

    Lives here rather than in the API layer because it *is* the cursor protocol, and there
    are two callers now — the post list and search — that must page identically or a fix to
    the off-by-one below would land in one of them and not the other.
    """
    posts = stream.queryset.order_by(f'-{stream.order_field}', '-uid')
    if cursor:
        posts = posts.filter(decode_cursor(cursor, stream.order_field))

    # one row more than asked for: whether it came back is what says there's a next page,
    # and it's free next to the COUNT query the alternative would cost
    window = list(posts[: limit + 1])
    items = window[:limit]
    has_more = len(window) > limit
    return {
        'items': items,
        'next_cursor': encode_cursor(items[-1], stream.order_field) if has_more else None,
    }


def _stream(user, predicate, order_field):
    return Stream(_annotate(user, Post.objects.filter(predicate)), order_field)


def _annotate(user, posts):
    """Attach the three fields that depend on who is asking.

    Subqueries, not joins. A source can sit in several of a user's feeds, so the rename is
    `[:1]` of the renamed ones — the first the user gave, in feed order — and SavedPost is
    unique per (user, post); none of them can multiply the post rows, which a
    `.filter(saves__user=…)` join paired with an `F('saves__…')` annotation quietly can,
    because Django's join reuse across filter and annotate is not the one you'd guess.
    """
    saved = SavedPost.objects.filter(user=user, post=OuterRef('pk'))
    renamed = FeedSource.objects.filter(feed__user=user, source=OuterRef('source')).exclude(name='')
    return posts.select_related('source').annotate(
        source_name=Subquery(renamed.order_by('feed__order', 'order').values('name')[:1]),
        saved_group=Subquery(saved.values('group')[:1]),
        saved_at=Subquery(saved.values('saved_at')[:1]),
    )


def _followed_sources(user):
    """Every source in any of the user's feeds — what they may open and save from."""
    return FeedSource.objects.filter(feed__user=user).values('source_id')


def _enabled_sources(user):
    """Sources switched on in at least one of the user's feeds — what All reads."""
    return FeedSource.objects.filter(feed__user=user, enabled=True).values('source_id')


def _saved_post_ids(user, group=None):
    saved = SavedPost.objects.filter(user=user)
    if group is not None:
        saved = saved.filter(group=group)
    return saved.values('post_id')
