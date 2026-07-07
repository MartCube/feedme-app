import type { FeedCandidate, FeedType } from './types'

// No backend yet: the query is ignored and each type returns the same fixed
// short list, after a ~1s delay so it feels like results arriving.
const RESULTS: Record<FeedType, FeedCandidate[]> = {
  website: [
    { name: 'CSS-Tricks', feed_url: 'https://css-tricks.com/feed/', site_url: 'https://css-tricks.com', type: 'website' },
    { name: 'Smashing Magazine', feed_url: 'https://www.smashingmagazine.com/feed/', site_url: 'https://www.smashingmagazine.com', type: 'website' },
    { name: 'A List Apart', feed_url: 'https://alistapart.com/main/feed/', site_url: 'https://alistapart.com', type: 'website' },
  ],
  youtube: [
    { name: 'Fireship', feed_url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCsBjURrPoezykLs9EqgamOA', site_url: 'https://www.youtube.com/@Fireship', type: 'youtube' },
    { name: 'Vue Mastery', feed_url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCG5UOTNKA1Fv5vBaMxg98rw', site_url: 'https://www.youtube.com/@VueMastery', type: 'youtube' },
    { name: 'Theo - t3.gg', feed_url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCbRP3c757lWg9M-U7TyEkXA', site_url: 'https://www.youtube.com/@t3dotgg', type: 'youtube' },
  ],
  reddit: [
    { name: 'r/vuejs', feed_url: 'https://www.reddit.com/r/vuejs/.rss', site_url: 'https://www.reddit.com/r/vuejs', type: 'reddit' },
    { name: 'r/webdev', feed_url: 'https://www.reddit.com/r/webdev/.rss', site_url: 'https://www.reddit.com/r/webdev', type: 'reddit' },
    { name: 'r/programming', feed_url: 'https://www.reddit.com/r/programming/.rss', site_url: 'https://www.reddit.com/r/programming', type: 'reddit' },
  ],
}

export function mockSearch(type: FeedType, _query: string): Promise<FeedCandidate[]> {
  return new Promise(resolve => setTimeout(() => resolve(RESULTS[type]), 1000))
}
