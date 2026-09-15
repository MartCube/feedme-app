"""YouTube's Data API, for the one thing its RSS can't do: find a channel by name.

Everything else about YouTube is plain RSS — polling reads `videos.xml?channel_id=`, and a
pasted channel URL or @handle resolves through the channel page (core/discover.py), so
neither spends any quota. This module is only the keyword case, and it is shaped by the
quota: 10,000 units a day per key, and `search.list` costs 100 of them, so roughly a
hundred searches. Every answer is cached, and a search that fails is not — an error would
otherwise be served for a day.

`fetch_search` is the one function that touches the network, so a test replaces exactly
that, the way test_discover.py replaces `discover.fetch_page`.
"""

import hashlib
import logging
import re
from dataclasses import dataclass

import requests
from django.conf import settings
from django.core.cache import cache

from .fetch import USER_AGENT

logger = logging.getLogger(__name__)

SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'
# (connect, read). The add wizard is waiting on this.
TIMEOUT = (5, 10)
# What fits the wizard's list; more channels named alike would not help anyone choose
MAX_RESULTS = 5
# A day, the same window the quota renews on: a name searched twice in a day costs once
CACHE_TTL = 24 * 60 * 60


class YouTubeUnavailable(Exception):
    """The Data API didn't answer — quota spent, key refused, or the network is down."""


@dataclass(frozen=True)
class Channel:
    """A search hit, as much of it as discovery needs to build a candidate from."""

    id: str
    title: str
    thumbnail: str


def is_configured():
    return bool(settings.YOUTUBE_API_KEY)


def search_channels(query):
    """Channels matching `query`, cached for a day. Raises YouTubeUnavailable."""
    # hashed rather than used raw: Django warns about spaces in a key, and a query is
    # spaces — plus a long one would blow the length limit the same warning guards
    key = 'youtube:search:' + hashlib.sha256(_normalise(query).encode()).hexdigest()
    channels = cache.get(key)
    if channels is None:
        try:
            body = fetch_search(query)
        except requests.RequestException as exc:
            # the exception's text carries the request URL, and the URL carries the key —
            # so the class name is all that gets logged
            logger.warning('youtube: search failed — %s', type(exc).__name__)
            raise YouTubeUnavailable() from exc
        channels = _channels(body)
        cache.set(key, channels, CACHE_TTL)
    return channels


def fetch_search(query):
    """This module's one network call: search.list, as the parsed JSON body."""
    response = requests.get(
        SEARCH_URL,
        params={
            'part': 'snippet',
            'type': 'channel',
            'q': query,
            'maxResults': MAX_RESULTS,
            'key': settings.YOUTUBE_API_KEY,
        },
        headers={'user-agent': USER_AGENT},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _channels(body):
    # sliced again here: asked for MAX_RESULTS, YouTube has answered with one more
    return [
        Channel(
            id=item['id']['channelId'],
            title=item['snippet']['title'],
            thumbnail=item['snippet']['thumbnails'].get('default', {}).get('url', ''),
        )
        for item in body.get('items', [])
        if item.get('id', {}).get('channelId')
    ][:MAX_RESULTS]


def _normalise(query):
    """One cache entry for `Ski Essentials` and ` ski   essentials `."""
    return re.sub(r'\s+', ' ', query.strip()).casefold()
