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

NOT_A_FEED = b'<html><body><h1>404 Not Found</h1></body></html>'
"""What a server hands back when the feed URL has quietly become an error page."""
