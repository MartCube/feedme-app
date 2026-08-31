"""uid → the posts behind it, and the cursor that pages through them.

`/feeds/{uid}/posts` is one polymorphic operation over five kinds of list, and the order it
tries them in is the frontend's exactly — all → saved → saved_* → folder_* → feed_*
(`app/utils/feed-title.ts`). Keeping that order in one module per side is what stops the two
from drifting.

Posts are global rows shared by every subscriber, so three of the fields the API returns
depend on who is asking: `feed_uid` (the caller's own handle on the post's source),
`saved_group` and `saved_at`. They arrive as correlated subqueries — see `_annotate`.

HttpError is raised from here rather than translated in the API layer: an unknown uid has
exactly one meaning (404) and a private exception type to carry it across one module
boundary would be machinery for nothing. T12's search.py resolves scopes the same way.
"""

import base64
from dataclasses import dataclass
from datetime import datetime

from django.db.models import OuterRef, Q, QuerySet, Subquery
from ninja.errors import HttpError

from .models import Feed, Folder, Post, SavedPost

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

    Every branch is rooted in the caller's own rows, so another user's folder or feed uid
    lands on the same 404 as one that never existed.
    """
    if uid == 'all':
        return _stream(user, Q(source__in=_subscribed_sources(user)), 'published_at')

    if uid == 'saved':
        return _stream(user, Q(id__in=_saved_post_ids(user)), 'saved_at')

    if uid.startswith(SAVED_PREFIX):
        group = uid.removeprefix(SAVED_PREFIX)
        if group not in SavedPost.Group.values:
            raise HttpError(404, f'no such feed: {uid}')
        return _stream(user, Q(id__in=_saved_post_ids(user, group)), 'saved_at')

    if uid.startswith('folder_'):
        folder = Folder.objects.filter(user=user, uid=uid).first()
        if folder is None:
            raise HttpError(404, f'no such feed: {uid}')
        # muted is filtered here, not on the feed: mute belongs to *this* folder's merged
        # read, so a muted member is absent here and still complete on its own feed page
        members = Feed.objects.filter(
            user=user, memberships__folder=folder, memberships__muted=False
        )
        return _stream(user, Q(source__in=members.values('source_id')), 'published_at')

    if uid.startswith('feed_'):
        feed = Feed.objects.filter(user=user, uid=uid).first()
        if feed is None:
            raise HttpError(404, f'no such feed: {uid}')
        return _stream(user, Q(source_id=feed.source_id), 'published_at')

    raise HttpError(404, f'no such feed: {uid}')


def visible_posts(user):
    """The posts a caller may open and save.

    Posts are global, so "is it mine" is not a user FK — it is this rule: a post from a
    source you subscribe to, or one you have already saved. The second half is what keeps a
    saved post readable after you unsubscribe from the feed it came from.
    """
    return _annotate(
        user,
        Post.objects.filter(
            Q(source__in=_subscribed_sources(user)) | Q(id__in=_saved_post_ids(user))
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

    # the list is ordered (order_field desc, uid desc), so "after" is a strict tuple compare
    return Q(**{f'{order_field}__lt': moment}) | Q(**{order_field: moment, 'uid__lt': uid})


def _stream(user, predicate, order_field):
    return Stream(_annotate(user, Post.objects.filter(predicate)), order_field)


def _annotate(user, posts):
    """Attach the three fields that depend on who is asking.

    Subqueries, not joins. Feed is unique per (user, source) and SavedPost per (user, post),
    so each resolves to exactly one row and none of them can multiply the post rows — which
    a `.filter(saves__user=…)` join paired with an `F('saves__…')` annotation quietly can,
    because Django's join reuse across filter and annotate is not the one you'd guess.
    """
    saved = SavedPost.objects.filter(user=user, post=OuterRef('pk'))
    return posts.annotate(
        feed_uid=Subquery(
            Feed.objects.filter(user=user, source=OuterRef('source')).values('uid')[:1]
        ),
        saved_group=Subquery(saved.values('group')[:1]),
        saved_at=Subquery(saved.values('saved_at')[:1]),
    )


def _subscribed_sources(user):
    return Feed.objects.filter(user=user).values('source_id')


def _saved_post_ids(user, group=None):
    saved = SavedPost.objects.filter(user=user)
    if group is not None:
        saved = saved.filter(group=group)
    return saved.values('post_id')
