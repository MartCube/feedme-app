# Data Model

This doc is the agreed model. The shapes below are **the API's** — since 2026-09-01 the app's
types are generated from the backend's OpenAPI document into `app/types/api.d.ts`
(`pnpm types:api`), and `app/assets/types.ts` is a thin alias layer over them, so a field named
here is the field on the wire. There is no mock data.

> **Persistence** lives in [backend.md](./backend.md): the server stores global
> `Source`/`Post` tables with a per-user `Feed`/`Folder`/`SavedPost` layer on top. A backend
> `Feed` (+ its `Source`) serializes to this `Feed` shape, and the backend mints the prefixed
> uids these docs assume. Three details were settled against the built models
> ([backend-roadmap.md](./backend-roadmap.md) § Contract resolutions) and are live in the app
> as of 2026-09-01:
>
> - **`Post.feed_uid` still exists**, but it is *derived* and **nullable**: backend posts
>   belong to a global `Source`, and the API resolves that source to **the requesting user's**
>   `Feed` uid. Merged streams (`all`, a folder) carry posts from many feeds, so each post
>   needs its own. It is `null` when the reader has no feed for that source — a saved post
>   outlives unsubscribing and is never hidden for want of a feed to point at.
> - **`Post.content` becomes `summary`** — what RSS gave us. Full article text is fetched
>   separately from `/posts/{uid}/article`, extracted on first open and cached globally.
> - **`feed_url` is read-only.** It lives on the shared global `Source`, so editing it would
>   repoint every other subscriber's feed. Renaming a feed changes `name` only.

## Feed

A subscribed source.

```ts
type FeedType = 'youtube' | 'reddit' | 'website'

interface Feed {
  uid: string       // stable id, e.g. 'feed_medium_vuejs'
  name: string      // display name, e.g. 'Vue.js on Medium' — the only editable field
  feed_url: string  // the RSS endpoint we pull items from (read-only: it's the Source's)
  site_url: string  // human-facing site; where "visit source" for the feed points
  icon_url: string  // the source's icon, when the feed advertised one — becomes `icon: string | null`
                    // (a 64px proxied square) in T15b, see images.md
  type: FeedType    // drives icon / small rendering differences
}
```

- `type` is used for per-source treatment: a YouTube item shows a video thumbnail, a website
  article shows body text, etc.
- `feed_url` is the machine endpoint (RSS); `site_url` is the human page.
- Everything but `name` belongs to the shared global `Source`, flattened onto the feed — a
  `Source` never surfaces as an entity of its own ([backend.md](./backend.md) § Vocabulary).

## Folder

A named container that **groups feeds** on the home screen. Membership lives on the folder
(a list of feed ids), which makes the relationship **many-to-many**: the same `feed_uid` can
appear in more than one folder. A feed is **loose** when its `uid` is in no folder.

```ts
interface Folder {
  uid: string                // stable id, e.g. 'folder_dev'
  name: string               // display name, e.g. 'Dev'
  feed_uids: string[]        // member feeds, in display order
  muted_feed_uids: string[]  // subset of feed_uids muted within THIS folder's merged read
}
```

- A folder is **read as a merged stream**: tapping it lists the newest-first posts of all its
  member feeds, except those in `muted_feed_uids`. Same shape as the Saved feed.
- **Mute is per-folder**, never global. A feed muted in one folder still contributes to any
  other folder it belongs to and is still fully readable on its own page. Muting only exists
  for feeds *inside* a folder.
- **Loose** = `uid` is in no folder's `feed_uids`. Loose feeds have no mute (only delete).
- Folders are not nested (no folder inside a folder), and the **Saved** feed is never inside a
  folder.

### Cascade rules

- **Remove from folder** — drops the `feed_uid` from one folder's `feed_uids` (and
  `muted_feed_uids`). The feed stays subscribed; it goes loose if it was in no other folder.
- **Delete feed** — unsubscribes the feed everywhere: removes it from every folder and from
  the feeds list.
- **Delete folder** — removes the folder **and unsubscribes its member feeds**, *except* any
  member that also belongs to another folder (those survive). Destructive, so it requires a
  confirmation that names how many feeds will be unsubscribed.

All three are **enforced by the API**, each with its own test _(2026-09-01)_: `DELETE /feeds/{uid}`
for the second, `PATCH` / `DELETE /folders/{uid}` for the other two. Two consequences of the
first rule worth naming: a member that leaves a folder loses its mute with it (mute only exists
*inside* a folder), and a feed that goes loose is given a fresh position at the **end** of the
top-level order rather than keeping the one it had before it joined.

## Post

An item belonging to a feed.

```ts
interface Post {
  uid: string             // stable id, e.g. 'post_a1b2c3'
  feed_uid: string | null // the reader's Feed for this post's source; null once unsubscribed
  title: string
  image: { src: string, srcset: string } | null  // ready <img> attributes, or null — see below
  published_at: string    // ISO 8601 timestamp
  post_url: string        // link to the original (or the YouTube watch page)
  summary: string         // what RSS gave us — HTML, from an arbitrary third party
  saved_group: SavedGroup | null  // which saved pile it's in, null when unsaved
}
```

- `image` _(shipped in T15a, 2026-09-22)_ is what the card and the post page put straight into
  an `<img>`: a signed, resized URL family from the image proxy, never the source's own URL, and
  `null` when the post has none. The frontend adds only `sizes`. How it is built, cached and
  later stored is [images.md](./images.md).
- `summary` is **not trusted markup**: it comes from whatever the feed published (Reddit wraps
  every post in a `<table>`), so the reader strips it to plain text rather than rendering it.
  The article text meant for reading is fetched separately from `/posts/{uid}/article`.
- `feed_uid` is per-reader and derived: merged streams (`all`, a folder, `saved`) carry posts
  from many feeds, so each post names its own.

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
- A saved post outlives unsubscribing from its source: it stays in the list, stays readable,
  and reports `feed_uid: null`.

## Relationships

```
Feed (1) ───< (many) Post         via Post.feed_uid -> Feed.uid (per reader, nullable)
Folder (many) >───< (many) Feed   via Folder.feed_uids contains Feed.uid
User (saved) ───< (many) Post     via Post.saved_group (null when unsaved)
```
