# Data Model

This doc is the agreed model. The shapes below are **the API's** — since 2026-09-01 the app's
types are generated from the backend's OpenAPI document into `app/types/api.d.ts`
(`pnpm types:api`), and `app/assets/types.ts` is a thin alias layer over them, so a field named
here is the field on the wire. There is no mock data.

> **Persistence** lives in [backend.md](./backend.md): the server stores global
> `Source`/`Post` tables with a per-user `Feed`/`FeedSource`/`SavedPost` layer on top. A backend
> `Feed` serializes to this `Feed` shape — its `FeedSource` rows flatten into `sources` — and
> the backend mints the prefixed uids these docs assume. **The model was remade on 2026-10-08:
> folders are gone, and a `Feed` is a group of sources** (the decision is in
> [backend.md](./backend.md) § Decision log). Details settled along the way
> ([backend-roadmap.md](./backend-roadmap.md) § Contract resolutions):
>
> - **`Post.source` replaces `Post.feed_uid`.** Backend posts belong to a global `Source`, and
>   merged streams (`all`, a feed, `saved`) carry posts from many sources, so each post names
>   its own — the uid, the reader's name for it, its type and its site. It is never null: a
>   saved post outlives its source leaving every feed, and keeps saying where it came from.
> - **`Post.content` becomes `summary`** — what RSS gave us. Full article text is fetched
>   separately from `/posts/{uid}/article`, extracted on first open and cached globally.
> - **A source's `feed_url` is never edited in place.** It lives on the shared global `Source`,
>   so editing it would repoint every other reader's feed. Changing a link in a feed instead
>   swaps *which source* that row holds (see Cascade rules).

## Feed

The user's own **group of sources** — a name, a description and an ordered list of sources.
It is what the home list shows and what the post list reads. A feed can hold one source or
many (a single-source feed is just a name in the list), and may be left empty.

```ts
interface Feed {
  uid: string          // stable id, e.g. 'feed_dev'
  name: string         // display name, e.g. 'Dev reading' — the user's
  description: string  // the user's, may be empty; seeded from the first source's own
  sources: Source[]    // in the feed's own order; may be empty
}
```

- A feed is **read as a merged stream**: tapping it lists the newest-first posts of its
  **enabled** sources. Same shape as the Saved feed.
- `name` and `description` are the user's to edit. A feed created from a source starts with
  that source's name and description unless the user supplies their own; a feed created
  without a source needs a name.
- Feeds are not nested, and the **Saved** feed is never a feed in this sense — it is app
  structure (`app/utils/saved.ts`), not a row the user owns.
- The home list is the feeds in display order. (`PUT /home/order` persists a reorder; no UI
  drives it yet — see [current-state.md](./current-state.md).)

## Source

One RSS endpoint — a website or blog, a YouTube channel, a subreddit. A `Source` is **global
and shared**: every user who follows it points at the same row, and it is polled once. What a
`Feed` shows for it is the source *as it sits in that feed*:

```ts
type FeedType = 'youtube' | 'reddit' | 'website'

interface Source {
  uid: string       // stable id, e.g. 'source_a1b2c3'
  name: string      // what the app shows: this feed's own name for it, else `title`
  title: string     // the source's own title — what a blank `name` falls back to
  type: FeedType    // drives icon / small rendering differences
  site_url: string  // human-facing site; where "visit source" points
  feed_url: string  // the RSS endpoint we pull items from
  icon: string | null  // a 64px proxied square, null when it has none — see images.md § Feed icons
  enabled: boolean  // on or off for THIS feed
}
```

- **One source can sit in several feeds**, many-to-many. Each placement carries its own `name`
  (the user's rename; blank means the source's `title`) and its own `enabled`.
- **On/off is per feed**, never global. A source off in one feed is still in that feed, still
  listed on its page, and still contributes to any other feed where it is on. **All feeds**
  (`all`) reads every source that is on in at least one feed.
- `type` is used for per-source treatment: a YouTube item plays a video, a website article
  shows body text, etc.
- `feed_url` is the machine endpoint (RSS); `site_url` is the human page.
- The source's `description` (its own RSS `<description>` / Atom `<subtitle>`, flattened to
  plain text) is backfilled at ingest like its title. It is not on the wire — it only seeds a
  new feed's description.

### Cascade rules

- **Remove a source from a feed** — drops that one placement (and its rename and on/off). The
  source stays in every other feed that has it. The feed stays too, even if it is now empty —
  the name and description the user wrote are theirs to keep.
- **Delete a feed** — removes the feed and all its placements. Any source left in **no** feed
  of anyone is deactivated (polling stops; the row and its posts are kept, so adding it again
  is instant). Saved posts always stay. Destructive, so it confirms first.
- **Change a source's link** — the new URL is resolved (fetched) to a *different* `Source`, and
  the placement is repointed to it, keeping its name and on/off. The old source is deactivated
  if nothing else holds it. A URL that isn't a feed changes nothing.

All three are **enforced by the API**, each with its own test: `DELETE /feeds/{uid}` for the
second, `DELETE` and `PATCH /feeds/{uid}/sources/{source_uid}` for the other two. A source that
is already in a feed cannot be added to it again.

## Post

An item belonging to a source.

```ts
interface Post {
  uid: string             // stable id, e.g. 'post_a1b2c3'
  source: {               // where it came from, named the reader's way
    uid: string
    name: string          // the reader's rename of that source in any feed (the first, in feed order), else its own title
    type: FeedType
    site_url: string
  }
  title: string
  image: { src: string, srcset: string } | null  // ready <img> attributes, or null — see below
  published_at: string    // ISO 8601 timestamp
  post_url: string        // link to the original (or the YouTube watch page)
  summary: string         // what RSS gave us — HTML, from an arbitrary third party
  video: { src: string, vertical: boolean } | null  // YouTube embed, null for everything else
  saved_group: SavedGroup | null  // which saved pile it's in, null when unsaved
}
```

- `image` _(shipped in T15a, 2026-09-22)_ is what the card and the post page put straight into
  an `<img>`: a signed, resized URL family from the image proxy, never the source's own URL, and
  `null` when the post has none. The frontend adds only `sizes`. How it is built, cached and
  later stored is [images.md](./images.md).
- `video` _(2026-09-28)_ is built from `post_url` for YouTube posts only: `src` is a
  privacy-enhanced (`youtube-nocookie.com`) embed, `vertical` is true for a Short (a `/shorts/`
  link). The post page plays it in place of the image.
- `summary` is **not trusted markup**: it comes from whatever the feed published (Reddit wraps
  every post in a `<table>`), so the reader strips it to plain text rather than rendering it.
  The article text meant for reading is fetched separately from `/posts/{uid}/article`.
- `source` is per-reader and always present: merged streams (`all`, a feed, `saved`) carry
  posts from many sources, so each post names its own. The reader may **open and save** a post
  whose source is in any of their feeds — on or off — or one they have already saved.

## Saved state

To support the **Saved** entry on the home list, a user can mark a post as saved — into one
of three fixed **groups**: Bookmarks, Favorites, Later (`app/utils/saved.ts` maps the home
rows' uids `saved_bookmarks` / `saved_favorites` / `saved_later` onto the API's group names).

```ts
type SavedGroup = 'bookmarks' | 'favorites' | 'later'
```

- Saved state is **per-user and server-side**. It rides along on the post itself as
  `saved_group`, so a card renders its save state without a second request, and it survives a
  reload and follows the account to another device.
- A post lives in exactly one group. `/feed/saved` lists every saved `Post` (all groups merged,
  newest **save** first — a pile you built, not a timeline you follow); `/feed/saved_*` lists
  one group, and `GET /home` carries the counts the home rows show.
- Saving on the Post page is a **toggle**, not a chooser: it saves into **Bookmarks** and
  unsaves from wherever the post was. Moving a post between groups is the same call, waiting
  on a UI for it.
- A saved post outlives its source leaving your feeds: it stays in the list, stays readable,
  and still names its `source`.

## Relationships

```
Source (1) ───< (many) Post         via Post.source.uid -> Source.uid
Feed (many) >───< (many) Source    via Feed.sources — each placement carries name + enabled
User (saved) ───< (many) Post       via Post.saved_group (null when unsaved)
```
