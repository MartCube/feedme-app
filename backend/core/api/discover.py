"""GET /discover — what the add wizard's search step asks.

Read-only and stateless: nothing is created by looking. A candidate becomes real only when
POST /feeds is called with its `feed_url`, which is why that field is the only one of these
the frontend has to keep — everything else is here to make the list pickable.

`core/discover.py` decides what a query means; this module is the HTTP shape around it,
plus the one thing discovery can't know because it has no user: which of these you already
follow.
"""

from dataclasses import asdict
from typing import Literal

from ninja import Router, Schema
from ninja.errors import HttpError

from .. import images
from ..discover import discover
from ..models import Source
from ..youtube import YouTubeUnavailable
from .errors import ErrorSchema

# The same Literal HomeFeedSchema uses, and for the same reason: the OpenAPI document then
# carries the three values, so the generated TypeScript keeps the FeedType union.
SourceType = Literal['website', 'youtube', 'reddit']

router = Router(tags=['feeds'])


class DiscoverResultSchema(Schema):
    """A candidate source: what the wizard shows, before it has a uid.

    The frontend's `FeedCandidate` is this schema, and it hands `feed_url` straight to
    POST /feeds (a new feed) or POST /feeds/{uid}/sources (an existing one).
    """

    name: str
    type: SourceType
    site_url: str
    feed_url: str
    # a signed proxy URL, or null — the app renders initials then (docs/images.md)
    icon: str | None
    # already in one of the caller's feeds — the wizard says so, and still lets it be picked:
    # a source can sit in several feeds
    already_subscribed: bool


@router.get(
    '/discover',
    response={
        200: list[DiscoverResultSchema],
        401: ErrorSchema,
        422: ErrorSchema,
        503: ErrorSchema,
    },
    operation_id='discover',
)
def discover_feeds(request, type: SourceType, q: str = ''):
    """Resolve a query into subscribable feeds. An unresolvable one is an empty list.

    Empty rather than an error: "nothing found" is the honest answer to a keyword the
    catalog doesn't have yet (T11d) as much as to a URL that hosts no feed, and neither is
    a failure the wizard should paint red. The 503 is the one thing that *is*: a YouTube
    search the Data API wouldn't answer, which is not the same as a name with no channel.

    `type` is the wizard's card, and it only decides how a *bare name* is read — `OnePiece`
    is a subreddit under the Reddit card and a channel search under YouTube. Every URL
    result is typed by its own URL, so a YouTube channel pasted under the Website card
    still comes back as YouTube rather than being quietly mislabelled.
    """
    try:
        candidates = discover(type, q)
    except YouTubeUnavailable:
        raise HttpError(503, 'YouTube search is unavailable right now.') from None
    # in any of the caller's feeds — the wizard still lets them add it to another one
    followed = set(
        Source.objects.filter(
            feeds__user=request.auth, feed_url__in=[c.feed_url for c in candidates]
        ).values_list('feed_url', flat=True)
    )
    return [
        DiscoverResultSchema(
            # the stored-form icon_url stays behind: the wire carries the signed `icon`
            **{k: v for k, v in asdict(candidate).items() if k != 'icon_url'},
            icon=images.icon(candidate.icon_url),
            already_subscribed=candidate.feed_url in followed,
        )
        for candidate in candidates
    ]
