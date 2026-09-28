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
from ..models import Feed
from ..youtube import YouTubeUnavailable
from .errors import ErrorSchema

# The same Literal HomeFeedSchema uses, and for the same reason: the OpenAPI document then
# carries the three values, so the generated TypeScript keeps the FeedType union.
SourceType = Literal['website', 'youtube', 'reddit']

router = Router(tags=['feeds'])


class DiscoverResultSchema(Schema):
    """A candidate feed. HomeFeedSchema minus the uid it hasn't earned, plus the flag.

    Field-for-field the same names as a real feed on purpose — the frontend's
    `FeedCandidate` is this schema, and it hands `feed_url` straight to POST /feeds.
    """

    name: str
    type: SourceType
    site_url: str
    feed_url: str
    # a signed proxy URL, or null — the app renders initials then (docs/images.md)
    icon: str | None
    # you can already follow something you searched for, and the wizard says so rather than
    # letting it be picked for a subscribe that answers 422
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
    followed = set(
        Feed.objects.filter(
            user=request.auth, source__feed_url__in=[c.feed_url for c in candidates]
        ).values_list('source__feed_url', flat=True)
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
