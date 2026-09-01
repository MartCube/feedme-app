import type { components } from '~/types/api'

// The app's shapes are the API's shapes: this file is a thin alias layer over
// the schema generated from the backend's OpenAPI document (`pnpm types:api`
// → app/types/api.d.ts). Components keep importing `~/assets/types`, and the
// two sides can no longer drift — a renamed backend field breaks typecheck.
type Schemas = components['schemas']

// A user's handle on a source: `name` is theirs, the rest is the shared
// Source's, flattened in (a Source never surfaces on its own — backend.md
// § Vocabulary).
export type Feed = Schemas['HomeFeedSchema']

// The kind of source a feed comes from. Drives small rendering differences
// (a YouTube item shows a video thumbnail + description, a website article
// shows body text, etc.).
export type FeedType = Feed['type']

// A named group of feeds on the home screen. Membership lives here
// (many-to-many: the same feed can be in several folders); a feed is
// "loose" when its uid is in no folder's feed_uids.
export type Folder = Schemas['HomeFolderSchema']

// `feed_uid` is nullable — a saved post outlives unsubscribing, so a saved
// list can carry a post whose source the reader no longer follows. `summary`
// is what RSS gave us; extracted article text is a separate field behind
// /posts/{uid}/article in T10. (backend-roadmap.md § Contract resolutions.)
export type Post = Schemas['PostSchema']

// Which saved pile a post is in. Named …Name because `SavedGroup` in
// app/utils/saved.ts is the home-list row that shows one.
export type SavedGroupName = NonNullable<Post['saved_group']>

// Response shapes the stores and composables load from.
export type Home = Schemas['HomeSchema']
export type PostPage = Schemas['PostPageSchema']
export type Settings = Schemas['SettingsSchema']
export type Me = Schemas['MeSchema']

// A search result before it is subscribed: a candidate feed with no uid yet.
// Becomes a Feed (uid minted by the backend) when the user adds it. Stays
// hand-written until T11's /discover gives it a schema of its own.
export type FeedCandidate = Omit<Feed, 'uid'>
