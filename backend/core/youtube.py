"""YouTube's Data API, for the one thing its RSS can't do: find a channel by name.

Everything else about YouTube is plain RSS — polling reads `videos.xml?channel_id=`, and a
pasted channel URL or @handle resolves through the channel page (core/discover.py), so
neither spends any quota. This module is only the keyword case, and it is shaped by the
quota: 10,000 units a day per key, and `search.list` costs 100 of them, so roughly a
hundred searches. Every answer is cached, and a search that fails is not — an error would
otherwise be served for a day. Each search also asks `channels.list` for the hits'
subscriber counts — one call for all of them, 1 unit — so the wizard can show how big a
channel is before it's picked.

`fetch_search` and `fetch_statistics` are the only functions that touch the network, so a
test replaces exactly those, the way test_discover.py replaces `discover.fetch_page`.
"""

import hashlib
import logging
import re
from dataclasses import dataclass, replace

import requests
from django.conf import settings
from django.core.cache import cache

from .fetch import USER_AGENT

logger = logging.getLogger(__name__)

SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'
CHANNELS_URL = 'https://www.googleapis.com/youtube/v3/channels'
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
    # None when the channel hides its count, or when the statistics call didn't answer
    subscribers: int | None = None


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
        counted = _with_subscribers(channels)
        # cached only with its counts: a statistics blip would otherwise hide them for a day
        if counted is not None:
            channels = counted
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


def fetch_statistics(channel_ids):
    """channels.list?part=statistics for every id at once, as the parsed JSON body."""
    response = requests.get(
        CHANNELS_URL,
        params={
            'part': 'statistics',
            'id': ','.join(channel_ids),
            'maxResults': MAX_RESULTS,
            'key': settings.YOUTUBE_API_KEY,
        },
        headers={'user-agent': USER_AGENT},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _with_subscribers(channels):
    """The channels with their subscriber counts, or None if the call failed.

    A failure doesn't fail the search — the hits are still worth showing — it just isn't
    cached, so the next search asks again.
    """
    if not channels:
        return channels
    try:
        body = fetch_statistics([channel.id for channel in channels])
    except requests.RequestException as exc:
        # same rule as the search: the URL carries the key, so only the class is logged
        logger.warning('youtube: statistics failed — %s', type(exc).__name__)
        return None
    counts = {}
    for item in body.get('items', []):
        statistics = item.get('statistics', {})
        if statistics.get('hiddenSubscriberCount') or 'subscriberCount' not in statistics:
            continue
        try:
            counts[item.get('id')] = int(statistics['subscriberCount'])
        except (TypeError, ValueError):
            continue
    return [replace(channel, subscribers=counts.get(channel.id)) for channel in channels]


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


# --- Polling: videos, not Shorts ------------------------------------------------------------

# The feed a YouTube source is stored under (discover.YOUTUBE_FEED); the channel id is `UC…`
CHANNEL_FEED = re.compile(
    r'^https://(?:www\.)?youtube\.com/feeds/videos\.xml\?channel_id=UC([\w-]+)$'
)
# The channel's uploads with the Shorts and the live streams left out: `UULF` + the id after `UC`
VIDEOS_FEED = 'https://www.youtube.com/feeds/videos.xml?playlist_id=UULF{}'


def videos_feed(feed_url):
    """The videos-only feed behind a channel feed, or None for any other URL.

    The channel feed mixes Shorts in — 11 of FORMULA 1's latest 15 entries were Shorts, which
    also pushes real videos out of a 15-entry window. YouTube keeps a playlist of the same
    uploads without them, under the same `yt:video:<id>` guids, so a source moved onto it keeps
    its posts. Only the URL polled changes; the channel feed stays the source's identity.
    """
    match = CHANNEL_FEED.match(feed_url or '')
    return VIDEOS_FEED.format(match[1]) if match else None


# --- Posts: the poster and the player -------------------------------------------------------

# A video id is 11 characters of the URL-safe base64 alphabet
VIDEO_ID = r'[A-Za-z0-9_-]{11}'
# What videos.xml hands every entry as its media:thumbnail
HQDEFAULT = re.compile(rf'^https://i\d?\.ytimg\.com/vi/({VIDEO_ID})/hqdefault\.jpg$')
# The two links videos.xml gives an entry: a Short is /shorts/<id>, anything else /watch?v=<id>
POST_URL = re.compile(rf'^https://(?:www\.)?youtube\.com/(?:watch\?v=|(shorts)/)({VIDEO_ID})')
# A lookup result is a fact about the video that doesn't change; a month keeps re-polls free
POSTER_CACHE_TTL = 30 * 24 * 60 * 60
# (connect, read) — the worker's call, before the ingest transaction
POSTER_TIMEOUT = (5, 5)


def poster(url):
    """The 1280 × 720 poster for a video, when it has one; otherwise the url unchanged.

    videos.xml only offers `hqdefault.jpg`: 480 × 360 with black bars, which leaves 480 × 270
    of picture — blurry on any card at 2x. `hq720.jpg` is the same frame at 1280 × 720 with no
    bars, and nearly every video has one (37 of 38 in the dev database; `maxresdefault` was
    missing on more). Nearly isn't all, and a 404 would cost the post its image, so it is
    checked before it is stored.
    """
    match = HQDEFAULT.match(url)
    if not match:
        return url
    video_id = match[1]
    key = f'youtube:hq720:{video_id}'
    exists = cache.get(key)
    if exists is None:
        try:
            exists = has_hq720(video_id)
        except requests.RequestException:
            # not cached: a network blip says nothing about the video
            return url
        cache.set(key, exists, POSTER_CACHE_TTL)
    return f'https://i.ytimg.com/vi/{video_id}/hq720.jpg' if exists else url


def has_hq720(video_id):
    """The one network call behind `poster`, so a test replaces exactly this."""
    response = requests.head(
        f'https://i.ytimg.com/vi/{video_id}/hq720.jpg',
        timeout=POSTER_TIMEOUT,
        headers={'User-Agent': USER_AGENT},
    )
    return response.status_code == 200


def video(post_url):
    """The player for a YouTube post: `{src, vertical}`, or None for anything else.

    Built from the post's own link, so it needs no column: the id is in it, and so is whether
    it's a Short. youtube-nocookie is YouTube's privacy-enhanced host — no cookies until the
    reader presses play. `playsinline` keeps iOS from forcing fullscreen; `rel=0` limits the
    end screen to the same channel.
    """
    match = POST_URL.match(post_url or '')
    if not match:
        return None
    shorts, video_id = match.groups()
    return {
        'src': f'https://www.youtube-nocookie.com/embed/{video_id}?playsinline=1&rel=0',
        'vertical': bool(shorts),
    }
