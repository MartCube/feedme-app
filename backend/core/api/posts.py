"""The post list every reader screen is built on, post detail, and the save toggle.

`core/postlist.py` owns which posts a uid means; this module is the HTTP shape around it —
the page window, the cursor, the three writes, and the article. `summary` is what RSS gave
us, kept deliberately apart from the article text `/posts/{uid}/article` extracts on demand
(docs/backend-roadmap.md § Contract resolutions, item 2); `core/extract.py` does that work.
"""

from datetime import datetime
from typing import Literal

from ninja import Query, Router, Schema, Status
from ninja.errors import HttpError

from .. import images
from ..extract import extract_article
from ..models import SavedPost
from ..postlist import page, resolve_stream, visible_posts
from .errors import ErrorSchema

# tagged `feeds`, not `posts`: from the app's side this whole module is reading a feed —
# the list endpoint's uid is polymorphic over all / saved / a saved group / a folder / a
# feed, and detail and save are what you do to something you found there. T7's subscription
# writes (POST /feeds, PATCH /feeds/{uid}) join this group.
router = Router(tags=['feeds'])

# 10 is the page the frontend's infinite scroll asks for. The cap exists only so a caller
# can't ask for the whole table at once; ninja rejects anything outside the range for free.
DEFAULT_LIMIT = 10
MAX_LIMIT = 100

# the same three values as SavedPost.Group, written out so the OpenAPI schema carries them
# and T6's generated TypeScript gets a union instead of `string`. A drift-guard test pins
# the two lists together.
SavedGroup = Literal['bookmarks', 'favorites', 'later']


class ImageSchema(Schema):
    """Ready <img> attributes — docs/images.md § Wire contract. `src` is the 960w URL, a safe
    default for a tag that ignores srcset; `srcset` is the finished attribute string, because
    which sizes exist is the backend's fact and sending it as data would let the two drift."""

    src: str
    srcset: str


class PostSchema(Schema):
    uid: str
    # null when the caller has no feed for this post's source: a saved post outlives
    # unsubscribing, and it is never hidden for want of a feed to point at
    feed_uid: str | None
    title: str
    post_url: str
    # null when the post has no image, or when this deployment has no imgproxy key. Named
    # `image` rather than reusing `image_url` with a new meaning: it is no longer a URL, and
    # the rename is what makes `pnpm types:api` plus typecheck find every consumer.
    image: ImageSchema | None
    summary: str
    published_at: datetime
    # null when the caller hasn't saved it — cards render the save state without a second
    # request, which is the whole point of carrying it on the post
    saved_group: SavedGroup | None

    @staticmethod
    def resolve_image(obj):
        return images.post_image(obj.image_url)


class PostPageSchema(Schema):
    items: list[PostSchema]
    # null means the end of the list
    next_cursor: str | None


class ArticleSchema(Schema):
    # two states on the wire where the column has three: `article_html` is null until
    # something tries, '' once a page was read and had no article in it. The reader falls
    # back the same way for both that and a page we couldn't reach — summary plus Open
    # source — so telling them apart would be a distinction nothing acts on.
    status: Literal['ok', 'unavailable']
    article_html: str | None


class SaveSchema(Schema):
    group: SavedGroup


class SavedSchema(Schema):
    group: SavedGroup
    saved_at: datetime


@router.get(
    '/feeds/{uid}/posts',
    response={200: PostPageSchema, 401: ErrorSchema, 404: ErrorSchema, 422: ErrorSchema},
    operation_id='list_posts',
)
def feed_posts(
    request,
    uid: str,
    cursor: str | None = None,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
):
    return page(resolve_stream(request.auth, uid), cursor, limit)


@router.get(
    '/posts/{uid}',
    response={200: PostSchema, 401: ErrorSchema, 404: ErrorSchema},
    operation_id='get_post',
)
def post_detail(request, uid: str):
    return _visible_post(request.auth, uid)


@router.get(
    '/posts/{uid}/article',
    response={200: ArticleSchema, 401: ErrorSchema, 404: ErrorSchema},
    operation_id='get_post_article',
)
def post_article(request, uid: str):
    """The full article, extracted on the first request for a post and cached after it.

    Synchronous with a hard timeout rather than a queued job — docs/backend.md's job table
    said the other thing, and docs/backend-roadmap.md § Decision log records the reversal.
    The reader is blocked on this either way, so queueing it would buy a free web thread at
    the cost of a polling loop and a third state on screen.

    The cache is global: `article_html` lives on the post, which is one row shared by every
    subscriber, so only the first person to open a post pays for the extraction.

    Anything short of an article is retried — `''` as much as `None`. A page that read as
    empty once (a bot-challenge page served as 200, a site mid-deploy) is not evidence about
    the article, and one bounded fetch per open is cheap next to a post that is wrong for
    everyone forever.
    """
    post = _visible_post(request.auth, uid)
    if not post.article_html:
        extract_article(post)
    html = post.article_html or ''
    return {'status': 'ok' if html else 'unavailable', 'article_html': html or None}


@router.put(
    '/posts/{uid}/save',
    response={200: SavedSchema, 401: ErrorSchema, 404: ErrorSchema, 422: ErrorSchema},
    operation_id='save_post',
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


@router.delete(
    '/posts/{uid}/save',
    response={204: None, 401: ErrorSchema, 404: ErrorSchema},
    operation_id='unsave_post',
)
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
