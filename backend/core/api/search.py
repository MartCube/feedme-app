"""GET /search — the same post list, narrowed by what you typed.

`core/search.py` decides what matches; this module is the HTTP shape around it, and there is
almost nothing to it because both halves already exist: the scope is `core/postlist.py`'s uid
resolution and the window is its cursor. That is the point — search is a filter on a stream,
not a second way to read posts, so the response is byte-for-byte a post page and the frontend
needs no new type to consume it.
"""

from ninja import Query, Router

from ..postlist import page
from ..search import search_stream
from .errors import ErrorSchema
from .posts import DEFAULT_LIMIT, MAX_LIMIT, PostPageSchema

# tagged `feeds` for the same reason the whole posts module is: from the app's side this is
# reading a feed. Grouping by what the caller is doing is what keeps the docs UI at four
# tags (docs/backend-roadmap.md § Decision log, 2026-09-01).
router = Router(tags=['feeds'])


@router.get(
    '/search',
    response={200: PostPageSchema, 401: ErrorSchema, 404: ErrorSchema, 422: ErrorSchema},
    operation_id='search_posts',
)
def search_posts(
    request,
    q: str,
    scope: str = 'all',
    cursor: str | None = None,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
):
    """Scoped post search. `scope` takes the same polymorphic uid the post list does.

    Engine-neutral by contract: no tsquery syntax on the way in, no rank on the way out.
    Replacing Postgres FTS with a dedicated engine later is a rewrite of `core/search.py`
    and nothing else — this signature is what makes that promise checkable.
    """
    return page(search_stream(request.auth, q, scope), cursor, limit)
