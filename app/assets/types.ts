// The kind of source a feed comes from. Drives small rendering
// differences (a YouTube item shows a video thumbnail + description,
// a website article shows body text, etc.).
export type FeedType = 'youtube' | 'reddit' | 'website'

export interface Feed {
  uid: string
  name: string
  feed_url: string // the RSS endpoint we pull from
  site_url: string // human-facing site, where "visit source" points
  type: FeedType
}

// A named group of feeds on the home screen. Membership lives here
// (many-to-many: the same feed can be in several folders); a feed is
// "loose" when its uid is in no folder's feed_uids.
export interface Folder {
  uid: string
  name: string
  feed_uids: string[] // member feeds, in display order
  muted_feed_uids: string[] // subset of feed_uids muted within THIS folder's merged read
}

export interface Post {
  uid: string
  feed_uid: string // FK -> Feed.uid
  title: string
  image_url: string // card image; for YouTube this is the video thumbnail
  published_at: string // ISO 8601
  post_url: string // link to the original (or the YouTube watch page)
  content: string // body we show on the detail page (whatever we have)
}

// A search result before it is subscribed: a candidate feed with no uid yet.
// Becomes a Feed (uid generated) when the user adds it.
export type FeedCandidate = Omit<Feed, 'uid'>
