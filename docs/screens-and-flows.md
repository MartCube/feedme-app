# Screens & Flows

This is the core spec: every screen, its purpose, what the user can do there, and where it
navigates. File references point at `app/pages/` and `app/components/`.

## Navigation map

```
                    ┌──────────────────────────┐
                    │  Feeds list  (index.vue) │
                    │  list of subscribed feeds│
                    └───┬──────────┬───────┬───┘
        tap a feed      │          │       │   navbar
                        ▼          │       └─► +  → Add drawer (add feed)
        ┌───────────────────────┐  │                     search input → results → add
        │  Feed page  (master)  │  │
        │  /feed/[uid]          │  └──────────► Settings (settings.vue)
        │  list of PostCards    │                /settings/{account, appearance,
        └───────────┬───────────┘                          about, report}
            tap a post
                    ▼
        ┌──────────────────────────────┐
        │  Post page  (detail)         │   actions: Save · Open source
        │  /feed/[uid]/post/[postUid]  │
        │  full readable post          │
        └──────────────────────────────┘

   uid can be 'saved' → the Saved feed, or a folder uid → its merged stream.
   Desktop: master + detail side by side. See screens 1, 6, and 7.
```

> **Routing.** Posts nest under feeds and Settings subpages nest under Settings, so the route
> *is* the navigation context. Master/detail by design: the parent (feed list / settings nav)
> stays mounted and renders the child into a `<NuxtPage/>` slot — one pane on mobile, two panes
> side by side on desktop. The two feed/post params must differ (`[uid]` vs `[postUid]`).
>
> ```
> pages/
>   index.vue                  → /
>   feed/
>     [uid].vue                → post list (master) + <NuxtPage/>;  uid: feed | 'saved' | folder
>     [uid]/
>       index.vue              → /feed/[uid]
>       post/[postUid].vue     → /feed/[uid]/post/[postUid]  (detail)
>   settings.vue               → settings nav (master) + <NuxtPage/>
>   settings/
>     index.vue · account.vue · appearance.vue · about.vue · report.vue
>   (add)                      → /add        design.vue → /design (plain layout)
>            /add renders the home component (pages:extend hook); the Add drawer opens over it,
>            mirroring settings. There is no add.vue page file.
> ```
>
> **The feed page is a polymorphic post-list view.** Its `[uid]` resolves to one of three
> things, and the same page + nested post route serve all three — there is no separate folder
> route. Resolve in a **fixed order** so the shared namespace never collides:
>
> 1. `saved` → the Saved feed (saved posts across feeds).
> 2. a **folder** uid (`folder_*`) → the folder's merged stream (member feeds minus muted).
> 3. otherwise a **feed** uid (`feed_*`) → that feed's own posts.
>
> Ids are prefixed (`feed_*`, `folder_*`, plus the literal `saved`) so resolution is
> unambiguous. Keep the page thin: it should delegate to a resolver (e.g. a `usePostList(uid)`
> composable returning `{ kind, title, posts }`) and just render the result, so feed / folder /
> saved differences live in the resolver, not in template conditionals.
>
> The current scaffold files (`pages/Feed.vue`, `pages/[Post].vue`, and the
> `SettingsAccount.vue` / `SettingsAbout.vue` *components*) move to match this tree.

---

## 1. Feeds list — `pages/index.vue`

**Purpose:** the home screen. Shows the **Saved** feed, the user's **folders**, and any
**loose** feeds (feeds not in a folder). Folders only exist here — they are created, read, and
edited from this screen.

**List order:** pinned **Saved** feed → **folders** → **loose feeds**.

**The user can:**
- See a **Saved** feed in the list → tapping it lists all posts the user has saved.
- See each **folder** as an **expandable/collapsible row** (collapsed: name + feed count).
  - **Expand** it → reveal its member feeds; muted members show greyed/off.
  - **Tap the folder row** → read the folder as a merged stream (`/feed/[uid]`, uid = the
    folder's uid).
  - **Tap a member feed** → that feed's page (`/feed/[uid]`).
- See each **loose feed** (name, type icon based on `Feed.type`) → **tap** → `/feed/[uid]`.
- **Create** via the navbar **+**: it opens the **Add drawer** directly (`→ /add`). Where
  **New folder** (name it + pick member feeds) is triggered from is undecided — the old
  **+** menu was dropped in favour of consistency with the settings drawer.
- **Edit** any feed or folder via a **context menu** — **long-press** on mobile, a **3-dot /
  overflow** affordance on desktop. Contents differ by row (see screen 7).
- Tap the **menu** icon (navbar) → open the Settings drawer.

**Data:** `feeds` and `folders` from `app/assets/data.ts` (later: the user's subscribed feeds
and folders), plus the **Saved** feed backed by saved state (the set of saved `Post.uid`s). A
feed is **loose** when its `uid` is in no folder's `feed_uids`.

**Navbar:** `components/Navbar.vue` provides the menu (`→ /settings`) and the **+** create menu
via `components/IconButton.vue`.

---

## 2. Feed page — `pages/feed/[uid].vue` (currently `Feed.vue`)

**Purpose:** show a post list for the selected `uid`. This is the **master** pane; on desktop
the selected post renders beside it (detail), on mobile it's full-screen. The page is
**polymorphic** — `uid` is a real feed, `saved`, or a folder (see screens 1 and 6, and the
Routing note's resolution order). The render is identical; only the post list it resolves
differs.

**The user can:**
- See a scrollable list of **PostCards** (`components/PostCard.vue`) for this feed.
- **Tap a post** → open the Post page (`/feed/[uid]/post/[postUid]`).
- Go **back** → Feeds list.

**Data:** the `Feed` matching the route `uid`, plus all `Post`s where
`post.feed_uid === feed.uid`. Posts shown newest-first by `published_at`. When `uid` is
`saved`, the list is every saved `Post`; when `uid` is a **folder**, the list is its member
feeds' posts merged (minus muted) — see screen 6.

**PostCard** shows: `image_url`, `title`, and `published_at` (and a type cue from the parent
feed). Tapping it opens the Post page.

---

## 3. Post page — `pages/feed/[uid]/post/[postUid].vue` (currently `[Post].vue`)

**Purpose:** read a single post in full. Nested under the feed, so it's the **detail** pane —
it renders beside the feed list on desktop and full-screen on mobile.

**The user can:**
- Read the post: `title`, `image_url`, formatted `published_at`, and `content`.
- **Save** the post (toggle) — adds/removes its `uid` from saved state. See
  [data-model.md](./data-model.md#saved-state-new--not-yet-in-code).
- **Open source** — opens `post.post_url` (the original article / YouTube watch page) in a
  new tab.
- Go **back** → the Feed page (the `[uid]` it was opened from — a real feed, or `saved`).

**Data:** the `Post` matching `postUid`; the route `uid` is the feed context it was opened in.

---

## 4. Add feed — `components/add/Drawer.vue` (bottom drawer)

**Purpose:** subscribe to a new feed. Reached from the navbar **+** (opens `/add` directly).
The drawer is hosted in the layout and mirrors the settings drawer: `/add` renders the home
component behind the sheet (`pages:extend` hook), and closing routes back to `/`.

**The user can:**
- Type in a **search input** at the top of the sheet.
- See a **list of results** below it — each result shows a type icon, name, and url, with an
  **add** affordance (`+`).
- **Add** a result to the feed list (or, later, a group).
- **Close** the drawer → returns to `/`.

**State today:** the drawer + rough layout exist as a **visual demonstration only** — the input
and the `+` do nothing and the results are a hardcoded mock list. Not yet built: real search
(or single-URL paste + type detection `youtube` | `reddit` | `website`), the add action, choosing
feed-list vs group as the destination, and form validation via the installed **VeeValidate + Zod**
stack.

---

## 5. Settings — `pages/settings.vue` + nested subpages

**Purpose:** account, appearance, app info, and support. Same master/detail shape as feeds: the
settings nav is the **master**, the chosen subpage is the **detail** — a drawer on mobile, two
panes on desktop. Each subpage is its own route (not in-drawer component state).

**Subpages:**
- **Account** — `/settings/account` — how you're signed in (Google / Apple), member since, etc.
- **Appearance** — `/settings/appearance` — card style, font size, theme (see
  [product-overview.md → Planned](./product-overview.md#planned-not-now)).
- **About** — `/settings/about` — app info.
- **Report an issue** — `/settings/report`.

The **Design system** page (`pages/design.vue`, `plain` layout) is a separate full page at
`/design`, not a settings subpage.

**The user can:**
- Open any subpage from the settings nav; navigate between them with **page-level** transitions.
- Go **back** → closes Settings (mobile) / returns to the nav (desktop).

**State today:** the existing drawer + slide animations were a demo built on component state;
they get reworked as Nuxt page transitions to match the routed structure.

---

## 6. Folder read — `pages/feed/[uid].vue` (folder uid)

**Purpose:** read a folder as a single **merged stream**. This is **not a separate screen** — a
folder uid resolves through the same feed page (screen 2), exactly like `saved` does.

**The user can:**
- See a scrollable list of **PostCards** combining all of the folder's member feeds, **newest
  first**, with each card carrying its source feed's type cue.
- **Tap a post** → open the Post page (`/feed/[uid]/post/[postUid]`, uid = the folder's uid).
- Go **back** → Feeds list.

**Data:** the `Folder` matching the route `uid`, plus all `Post`s whose `feed_uid` is in
`folder.feed_uids` **and not** in `folder.muted_feed_uids`. Muted members are excluded here but
unaffected on their own feed pages and in other folders. (See the resolution order in the
Routing note: `saved` → folder → feed.)

---

## 7. Create & edit folders / feeds (from the home list)

**Create — navbar `+`:**
- **New feed** → the **+** opens the Add drawer at `/add` directly (screen 4).
- **New folder** → a route-backed drawer/page: enter a **name** and **pick member feeds**
  (multi-select from existing feeds). Confirm → the folder appears in the Feeds list. Same
  drawer-on-mobile / panel-on-desktop pattern as Add feed. **Entry point is undecided** — the
  old **+** menu that offered both was dropped; where folder creation is triggered from is a
  later design decision.

**Edit — context menu** (long-press on mobile; 3-dot / overflow on desktop). The menu depends
on what was pressed:

- **Folder row:**
  - **Rename** the folder.
  - **Edit feeds** — add/remove member feeds and **toggle per-folder mute** on members.
  - **Delete folder** — see cascade below.
- **Loose feed row:**
  - **Rename** the feed.
  - **Delete feed**. *(No mute — mute only exists inside a folder.)*
- **Feed row inside a folder:**
  - **Rename** the feed.
  - **Mute in this folder** (toggle) — excludes it from this folder's merged read only.
  - **Remove from this folder** — unlinks it here; it stays subscribed (goes loose if it was
    in no other folder).
  - **Delete feed**.

**Destructive cascade** (mirrors [data-model.md](./data-model.md#cascade-rules)):
- **Remove from folder** — unlinks one membership; feed stays subscribed.
- **Delete feed** — unsubscribes the feed everywhere (all folders + the list).
- **Delete folder** — removes the folder **and unsubscribes its member feeds**, *except* any
  member that also belongs to another folder. This is destructive, so it asks for a
  **confirmation that names how many feeds will be unsubscribed**.

---

## Cross-screen behaviors

- **Back navigation** follows the route nesting: Post → Feed → Feeds list (where "Feed" is the
  `/feed/[uid]` it opened from — a real feed, `saved`, or a folder), and Settings subpage →
  Settings → wherever it opened from. Add / New-folder close back to `/`.
- **Master/detail by viewport:** the same nested routes present as one pane on mobile and two
  panes (master + detail) on desktop — see the Routing note above. Layout is a presentation
  concern; the routes don't change.
- **Type-aware rendering:** `Feed.type` drives small differences (YouTube thumbnail vs.
  article body), but the layout and interactions are the same across types.
