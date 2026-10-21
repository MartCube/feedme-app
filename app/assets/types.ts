import type { components } from '~/types/api'

// The app's shapes are the API's shapes: this file is a thin alias layer over
// the schema generated from the backend's OpenAPI document (`pnpm types:api`
// → app/types/api.d.ts). Components keep importing `~/assets/types`, and the
// two sides can no longer drift — a renamed backend field breaks typecheck.
type Schemas = components['schemas']

// A user's named group of sources — one or many — and what the home list
// shows. `name` and `description` are theirs; `sources` is in the feed's own
// order, each with its on/off for this feed (docs/data-model.md § Feed).
export type Feed = Schemas['HomeFeedSchema']

// One source inside one feed: an RSS endpoint, shared by everyone who follows
// it, plus this feed's name for it (`name` — the user's rename, or the
// source's own `title`) and whether it's switched on here.
export type Source = Schemas['FeedSourceSchema']

// The kind of source. Drives small rendering differences (a YouTube post
// plays inline, a website post reads as an article).
export type FeedType = Source['type']

// `source` is where the post came from, named the caller's way — present
// even on a saved post whose source has left every feed. `summary` is what RSS
// gave us; the extracted article is a separate field behind
// /posts/{uid}/article.
export type Post = Schemas['PostSchema']

// Which saved pile a post is in. The backend keeps three; the app shows one
// Saved list and files every save under the default (composables/usePost.ts).
export type SavedGroupName = NonNullable<Post['saved_group']>

// Ready <img> attributes for a post image (docs/images.md § Wire contract):
// the backend signs them, the app puts them in the tag. Null on a Post means
// no image, or a deployment with no proxy key — the card renders compact.
export type PostImage = NonNullable<Post['image']>

// A YouTube post's player: the ready embed src, and whether it's a vertical
// Short. Built by the backend like the image attributes; null on a Post that
// isn't a video.
export type PostVideo = NonNullable<Post['video']>

// GET /posts/{uid}/article: the extracted article, sanitised server-side
// against the backend's own allowlist (core/extract.py) — the one field the
// app renders as markup. `unavailable` is a fallback, not an error: the reader
// shows the summary instead.
export type Article = Schemas['ArticleSchema']

// Response shapes the stores and composables load from.
export type Home = Schemas['HomeSchema']
export type PostPage = Schemas['PostPageSchema']
export type Settings = Schemas['SettingsSchema']
export type Me = Schemas['MeSchema']

// What POST /auth/google answers with: our own bearer token, and nothing else.
// The profile comes from /me afterwards, the same way the dev-token path gets it.
export type TokenResponse = Schemas['TokenSchema']

// A search result before it is added: a candidate source with no uid yet.
// Joins a feed (POST /feeds or /feeds/{uid}/sources) by its `feed_url`.
// `already_subscribed` means it's in one of your feeds already — it can still
// go into another.
export type FeedCandidate = Schemas['DiscoverResultSchema']
