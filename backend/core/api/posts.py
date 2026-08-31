"""The post list every reader screen is built on, post detail, and the save toggle.

`core/postlist.py` owns which posts a uid means; this module is the HTTP shape around it —
the page window, the cursor, and the three writes. `summary` is what RSS gave us; the
extracted article text is a separate field behind `/posts/{uid}/article` in T10
(docs/backend-roadmap.md § Contract resolutions, item 2).
"""

from datetime import datetime
from typing import Literal

from ninja import Query, Router, Schema, Status
from ninja.errors import HttpError

from ..models import SavedPost
from ..postlist import decode_cursor, encode_cursor, resolve_stream, visible_posts
from .errors import ErrorSchema

router = Router()

# 10 is the page the frontend's infinite scroll asks for. The cap exists only so a caller
# can't ask for the whole table at once; ninja rejects anything outside the range for free.
DEFAULT_LIMIT = 10
MAX_LIMIT = 100

# the same three values as SavedPost.Group, written out so the OpenAPI schema carries them
# and T6's generated TypeScript gets a union instead of `string`. A drift-guard test pins
# the two lists together.
SavedGroup = Literal['bookmarks', 'favorites', 'later']


class PostSchema(Schema):
    uid: str
    # null when the caller has no feed for this post's source: a saved post outlives
    # unsubscribing, and it is never hidden for want of a feed to point at
    feed_uid: str | None
    title: str
    post_url: str
    image_url: str
    summary: str
    published_at: datetime
    # null when the caller hasn't saved it — cards render the save state without a second
    # request, which is the whole point of carrying it on the post
    saved_group: SavedGroup | None


class PostPageSchema(Schema):
    items: list[PostSchema]
    # null means the end of the list
    next_cursor: str | None


class SaveSchema(Schema):
    group: SavedGroup


class SavedSchema(Schema):
    group: SavedGroup
    saved_at: datetime


@router.get(
    '/feeds/{uid}/posts',
    response={200: PostPageSchema, 401: ErrorSchema, 404: ErrorSchema, 422: ErrorSchema},
)
def feed_posts(
    request,
    uid: str,
    cursor: str | None = None,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
):
    stream = resolve_stream(request.auth, uid)
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


@router.get('/posts/{uid}', response={200: PostSchema, 401: ErrorSchema, 404: ErrorSchema})
def post_detail(request, uid: str):
    return _visible_post(request.auth, uid)


@router.put(
    '/posts/{uid}/save',
    response={200: SavedSchema, 401: ErrorSchema, 404: ErrorSchema, 422: ErrorSchema},
)
def save_post(request, uid: str, payload: SaveSchema):
    post = _visible_post(request.auth, uid)
    # an upsert, so moving between groups is this same call (SavedPost is unique per
    # user+post). saved_at is auto_now_add and so survives a move: it means "when this
    # entered your saved pile", which a change of group doesn't reset.
    saved, _ = SavedPost.objects.update_or_create(
        user=request.auth, post=post, defaults={'group': payload.group}
    )
    return saved


@router.delete('/posts/{uid}/save', response={204: None, 401: ErrorSchema, 404: ErrorSchema})
def unsave_post(request, uid: str):
    post = _visible_post(request.auth, uid)
    # idempotent on purpose — a double-tapped save toggle shouldn't raise
    SavedPost.objects.filter(user=request.auth, post=post).delete()
    return Status(204, None)


def _visible_post(user, uid):
    post = visible_posts(user).filter(uid=uid).first()
    if post is None:
        # 404 rather than 403 for a post that exists but isn't yours to see: which of the
        # two it is isn't the caller's business
        raise HttpError(404, f'no such post: {uid}')
    return post
