"""Feed bodies for the ingest tests, trimmed from what the real sources actually serve.

Not a test module — pytest only collects `test_*.py`. Kept out of the test file so the
assertions stay readable next to each other.
"""

RSS_BLOG = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Vuejs on Medium</title>
  <link>https://medium.com/tag/vuejs</link>
  <image><url>https://cdn.example.com/icon.png</url><link>https://medium.com/tag/vuejs</link><title>Vuejs</title></image>
  <item>
    <title>The Composition API</title>
    <link>https://medium.com/p/one?source=rss</link>
    <guid isPermaLink="false">https://medium.com/p/one</guid>
    <pubDate>Mon, 24 Aug 2026 20:36:01 GMT</pubDate>
    <description>&lt;p&gt;Why script setup is the cleanest way&lt;/p&gt;</description>
  </item>
  <item>
    <title>Reactivity in depth</title>
    <link>https://medium.com/p/two</link>
    <guid isPermaLink="false">https://medium.com/p/two</guid>
    <pubDate>Sun, 23 Aug 2026 09:00:00 GMT</pubDate>
    <description>Refs and proxies</description>
    <enclosure url="https://cdn.example.com/two.jpg" type="image/jpeg" length="1234"/>
  </item>
</channel></rss>
"""

# same two guids, one retitled, plus a third item
RSS_BLOG_UPDATED = RSS_BLOG.replace(
    b'<title>The Composition API</title>',
    b'<title>The Composition API, revised</title>',
).replace(
    b'</channel></rss>',
    b"""  <item>
    <title>Suspense, finally</title>
    <link>https://medium.com/p/three</link>
    <guid isPermaLink="false">https://medium.com/p/three</guid>
    <pubDate>Tue, 25 Aug 2026 08:00:00 GMT</pubDate>
    <description>Async components</description>
  </item>
</channel></rss>""",
)

ATOM_YOUTUBE = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/"
      xmlns:yt="http://www.youtube.com/xml/schemas/2015">
  <title>SkiEssentials</title>
  <link rel="alternate" href="https://www.youtube.com/channel/UCgij"/>
  <entry>
    <id>yt:video:H14_F7bGgzg</id>
    <yt:videoId>H14_F7bGgzg</yt:videoId>
    <title>Top 5 Fridays - Episode 268</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=H14_F7bGgzg"/>
    <published>2026-08-21T21:06:18+00:00</published>
    <updated>2026-08-22T15:28:19+00:00</updated>
    <media:group>
      <media:description>The week's ski industry news</media:description>
      <media:thumbnail url="https://i1.ytimg.com/vi/H14_F7bGgzg/hqdefault.jpg" width="480" height="360"/>
      <media:content url="https://www.youtube.com/v/H14_F7bGgzg" type="application/x-shockwave-flash"/>
    </media:group>
  </entry>
</feed>
"""

# The same channel's videos-only feed: a playlist titled "Videos", with no alternate link, whose
# author is the channel
ATOM_YOUTUBE_VIDEOS = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/"
      xmlns="http://www.w3.org/2005/Atom">
  <link rel="self" href="http://www.youtube.com/feeds/videos.xml?playlist_id=UULFgij"/>
  <id>yt:playlist:UULFgij</id>
  <title>Videos</title>
  <author>
    <name>SkiEssentials</name>
    <uri>https://www.youtube.com/channel/UCgij</uri>
  </author>
  <entry>
    <id>yt:video:H14_F7bGgzg</id>
    <title>Top 5 Fridays - Episode 268</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=H14_F7bGgzg"/>
    <published>2026-08-21T21:06:18+00:00</published>
  </entry>
</feed>
"""

# A channel feed carrying a Short beside a video
ATOM_YOUTUBE_WITH_SHORT = ATOM_YOUTUBE.replace(
    b'</feed>',
    b"""  <entry>
    <id>yt:video:Ab3_x9KqLmZ</id>
    <title>One turn, slowed down</title>
    <link rel="alternate" href="https://www.youtube.com/shorts/Ab3_x9KqLmZ"/>
    <published>2026-08-22T10:00:00+00:00</published>
  </entry>
</feed>""",
)

ATOM_REDDIT = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>One Piece</title>
  <icon>https://www.redditstatic.com/icon.png</icon>
  <link rel="alternate" href="https://www.reddit.com/r/OnePiece/"/>
  <entry>
    <id>https://www.reddit.com/r/OnePiece/t3_1vw9fff</id>
    <title>Chapter 1191 Official Release Discussion</title>
    <link rel="alternate" href="https://www.reddit.com/r/OnePiece/comments/1vw9fff/chapter/"/>
    <updated>2026-08-23T15:00:07+00:00</updated>
    <content type="html">&lt;div class="md"&gt;&lt;p&gt;Chapter 1191 is out&lt;/p&gt;&lt;/div&gt;</content>
  </entry>
</feed>
"""

# an entry with no link at all — nothing to point a card at, so it gets skipped
RSS_NO_LINK = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Broken</title>
  <item><title>Linkless</title><description>no link, no guid</description></item>
  <item><title>Fine</title><link>https://example.com/ok</link></item>
</channel></rss>
"""

# no date anywhere — published_at has to fall back
RSS_NO_DATE = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Undated</title>
  <item><title>Whenever</title><link>https://example.com/whenever</link></item>
</channel></rss>
"""

# An archive feed: everything the blog ever published, in one document. nuxt.com/blog/rss.xml
# is the real one this is trimmed from — 51 entries reaching back to 2019, which is what put
# ingest and retention in a loop over the same rows until _upsert_posts learned the window.
RSS_ARCHIVE = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>The Nuxt Blog</title>
  <link>https://nuxt.com/blog</link>
  <item>
    <title>Announcing Nuxt 4</title>
    <link>https://nuxt.com/blog/v4</link>
    <guid isPermaLink="false">https://nuxt.com/blog/v4</guid>
    <pubDate>Wed, 02 Sep 2026 09:00:00 GMT</pubDate>
    <description>Fresh enough to keep</description>
  </item>
  <item>
    <title>Introducing Smart Prefetching</title>
    <link>https://nuxt.com/blog/introducing-smart-prefetching</link>
    <guid isPermaLink="false">https://nuxt.com/blog/introducing-smart-prefetching</guid>
    <pubDate>Mon, 28 Jan 2019 00:00:00 GMT</pubDate>
    <description>Years past any retention window</description>
  </item>
</channel></rss>
"""

NOT_A_FEED = b'<html><body><h1>404 Not Found</h1></body></html>'
"""What a server hands back when the feed URL has quietly become an error page."""

# Content a feed is free to serve and Postgres is free to reject. A NUL byte anywhere in a
# text column is a DataError, which is not a parse problem feedparser can shield us from —
# it arrives as perfectly valid XML (&#0; is not, so it is spliced in as a raw byte).
RSS_NUL_BYTES = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Nul\x00lish</title>
  <item><title>Bad\x00 title</title><link>https://example.com/nul</link><description>bad\x00 body</description></item>
</channel></rss>
"""

# Links the reader would render as hrefs. Only http(s) is a post; the rest is not a place
# a feed item can live, whatever the markup says.
RSS_ODD_SCHEMES = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel>
  <title>Odd</title>
  <link>javascript:alert(1)</link>
  <image><url>data:image/png;base64,AAAA</url><title>Odd</title><link>https://example.com/</link></image>
  <item><title>Script</title><link>javascript:alert(1)</link></item>
  <item><title>Mail</title><link>mailto:someone@example.com</link></item>
  <item><title>Fine</title><link>https://example.com/fine</link><media:thumbnail url="data:image/png;base64,AAAA"/></item>
</channel></rss>
"""

# A post dated ten years out — a buggy or hostile feed pinning itself to the top of every list.
RSS_FUTURE_DATE = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Tomorrow</title>
  <item><title>Not yet</title><link>https://example.com/future</link><pubDate>Mon, 01 Jan 2036 00:00:00 GMT</pubDate></item>
</channel></rss>
"""
