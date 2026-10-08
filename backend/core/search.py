"""Finding a post inside a list you are already looking at.

The engine is Postgres — a generated tsvector on Post plus a trigram index on the title —
and this module exists so that stays true of *only* this module. docs/backend.md § Search's
Elasticsearch upgrade path is a one-module swap precisely because nothing else references
the column; `core/models.py` declares it and nothing reads it but the query below.

Scoping is not reimplemented here. `postlist.resolve_stream` already turns a uid into the
posts behind it, and reusing it verbatim is what makes searching inside a feed skip the
sources switched off *in that feed*, makes another user's uid 404 rather than leak, and carries the
three per-caller annotations a post response needs. Search is that stream with one more
WHERE on it.
"""

from django.contrib.postgres.search import SearchQuery
from django.db.models import Q

from .models import SEARCH_CONFIG
from .postlist import Stream, resolve_stream


def search_stream(user, q, scope):
    """The posts in `scope` matching `q`, ordered by the stream's own column.

    Keeping `resolve_stream`'s `order_field` rather than forcing `published_at` means a
    search inside `saved` reads newest-*saved* first, like the saved list it was opened
    from. Results are ordered by recency, not relevance: that reuses T5's cursor unchanged
    instead of growing a second, rank-keyed one beside it. The vector still carries the
    title-over-summary weights, so ranking later is an order_by, not a migration.
    """
    stream = resolve_stream(user, scope)
    # the scope is validated either way — a bad uid is wrong regardless of what was typed.
    # The NUL is dropped rather than refused: Postgres rejects it in a parameter as loudly
    # as in a column, and a search is not a write worth a 422 over one byte.
    query = (q or '').replace('\x00', '').strip()
    if not query:
        # "you typed nothing" is not a client error worth a 422, and .none() costs no query
        return Stream(stream.queryset.none(), stream.order_field)
    return Stream(stream.queryset.filter(_matches(query)), stream.order_field)


def _matches(q):
    """Whole-word OR partial-word — the two halves answer different questions.

    Full-text covers title and summary, stemmed, so `routers` finds `router`. It cannot
    find `rout` inside `router`: FTS matches whole lexemes, and no amount of tuning changes
    that. The trigram half is that missing case, and it is title-only on purpose — `summary`
    is arbitrary third-party HTML (Reddit wraps a whole <table> around every post), so
    substring-matching it would match markup. The tsvector already covers summary
    whole-word, and Postgres's default parser drops `tag` tokens, so the vector holds the
    text and not the tags.

    `websearch` is load-bearing rather than a preference: it is the one search_type that
    treats its input as something a person typed, so an unbalanced quote or a stray `&`
    comes back empty instead of raising out of the request as a 500.
    """
    return Q(search=SearchQuery(q, config=SEARCH_CONFIG, search_type='websearch')) | Q(
        title__icontains=q
    )
