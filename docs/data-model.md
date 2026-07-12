# Data Model

The current type definitions live in `app/assets/types.ts`; mock data lives in
`app/assets/data.ts`. This doc is the agreed model — including the **saved-posts** state,
which is not yet in code.

## Feed

A subscribed source.

```ts
type FeedType = 'youtube' | 'reddit' | 'website'

interface Feed {
  uid: string       // stable id, e.g. 'feed_medium_vuejs'
  name: string      // display name, e.g. 'Vue.js on Medium'
  feed_url: string  // the RSS endpoint we pull items from
  site_url: string  // human-facing site; where "visit source" for the feed points
  type: FeedType    // drives icon / small rendering differences
}
```

- `type` is used for per-source treatment: a YouTube item shows a video thumbnail, a website
  article shows body text, etc.
- `feed_url` is the machine endpoint (RSS); `site_url` is the human page.

## Folder *(new — not yet in code)*

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

## Post

An item belonging to a feed.

```ts
interface Post {
  uid: string          // stable id, e.g. 'art_med_1'
  feed_uid: string     // FK -> Feed.uid (which feed this belongs to)
  title: string
  image_url: string    // card image; for YouTube this is the video thumbnail
  published_at: string // ISO 8601 timestamp
  post_url: string     // link to the original (or the YouTube watch page)
  content: string      // body shown on the post detail page (whatever we have)
}
```

## Saved state *(new — not yet in code)*

To support the **Saved** entry on the home list, a user can mark a post as saved — into one
of three fixed **groups**: Bookmarks, Favorites, Later (defined in `app/utils/saved.ts`,
uids `saved_bookmarks` / `saved_favorites` / `saved_later`). The simplest model is a map
from post id to its group:

```ts
// e.g. a Pinia store: useSavedStore()
saved: Map<string, string>   // Post.uid → the saved-group uid it was saved into
```

- "Saved" is a per-user flag derived against `Post.uid`; a post lives in exactly one group.
- `/feed/saved` lists every saved `Post` (all groups merged); `/feed/saved_*` lists one group.
- Toggling save on the Post page adds/removes the post's `uid` (group picking TBD).

When persistence is introduced, saved state should survive reloads (local storage at
minimum, backend later — see [current-state.md](./current-state.md)).

## Relationships

```
Feed (1) ───< (many) Post         via Post.feed_uid -> Feed.uid
Folder (many) >───< (many) Feed   via Folder.feed_uids contains Feed.uid
User (saved) ───< (many) Post     via saved maps Post.uid → a saved-group uid
```

## Mock data today

`app/assets/data.ts` ships:

- **3 feeds:** `feed_medium_vuejs` (website), `feed_youtube` (youtube),
  `feed_reddit_onepiece` (reddit).
- **15 posts:** 5 per feed.
- **Folders:** none yet — mock folders are added with the folders feature.

This is the data the screens should be built against until real RSS fetching lands.
