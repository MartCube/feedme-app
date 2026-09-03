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
        │  /feed/[uid]          │  └──────────► Settings (/settings/:panel?)
        │  list of PostCards    │                /settings/{account, appearance,
        └───────────┬───────────┘                          about, report}
            tap a post
                    ▼
        ┌──────────────────────────────┐
        │  Post page  (detail)         │   actions: Save · Open source
        │  /feed/[uid]/post/[postUid]  │
        │  full readable post          │
        └──────────────────────────────┘

   uid can be 'all' → every followed feed merged, 'saved' → the Saved feed,
   or a folder uid → its merged stream.
   Desktop: sidebar + posts pane + post pane side by side. See screens 1, 6, and 7.

   Signed out, every route above redirects to /login (screen 0) — there is no
   anonymous surface. Signing out, or a session going stale mid-use, lands there too.
```

> **Routing.** Posts nest under feeds and Settings subpages nest under Settings, so the route
> *is* the navigation context — but that context now drives **two different renderers**
> instead of one nested-page tree:
>
> - **Mobile** (< 1024px): each route is its own page, and `feed/[uid].vue` is a bare
>   `<NuxtPage/>` passthrough to its `index.vue` / `post/[postUid].vue` children — one pane at
>   a time, sliding like a navigation stack.
> - **Desktop** (≥ 1024px): `app/layouts/default.vue` renders `DesktopShell` instead of
>   `<NuxtPage/>` at all. The shell reads the live route (`useRouter().currentRoute`, since
>   Nuxt's `useRoute()` only resyncs when a `<NuxtPage/>` resolves and the shell renders none)
>   and composes three columns directly from it and the `feeds`/`settings` stores: a sidebar
>   (feed list, plus standing Add feed / Settings links), a posts pane, and a post pane.
>   Settings/Add/Edit render as a content area sliding in over the two reading panes instead of
>   a drawer — as a master–detail pair where there's a list to sit beside (Settings, folder
>   editing) and single-pane where there isn't (Add, loose-feed editing). **The routes and
>   `pages:extend` records are identical on both viewports** — layout is purely a presentation
>   concern, nothing about navigation or the route tree changes. (This settles the layout half
>   of the routing decision toward layout-composed panes rather than a nested-`<NuxtPage/>`
>   master/detail tree — see [current-state.md](./current-state.md#resolved-decisions).)
>
> The two feed/post params must differ (`[uid]` vs `[postUid]`).
>
> ```
> pages/
>   index.vue                  → /
>   login.vue                  → /login   (screen 0; the one route the global auth guard
>                                          lets through, and the one that renders no layout)
>   feed/
>     [uid].vue                → mobile: <NuxtPage/> passthrough;  uid: feed | 'all' | 'saved' | folder
>     [uid]/
>       index.vue              → /feed/[uid]              (post list)
>       post/[postUid].vue     → /feed/[uid]/post/[postUid]  (post)
>
> pages:extend (nuxt.config.ts) adds these paths, all rendering the SAME index.vue component
> (the home page, kept mounted behind a drawer on mobile / behind the content overlay on
> desktop) — there are no separate settings.vue / settings/*.vue page files:
>   /settings/:panel?          → SettingsDrawer (mobile) / DesktopContentOverlay (desktop)
>   /add                       → AddDrawer (mobile) / DesktopContentOverlay (desktop)
>   /edit/:uid, /edit/:uid/feed/:feedUid, /edit/:uid/add, /edit/:uid/add/input,
>   /edit/:uid/delete, /edit/:uid/feed/:feedUid/delete
>                              → EditDrawer (mobile) / DesktopContentOverlay (desktop)
> ```
>
> **The feed page is a polymorphic post-list view.** Its `[uid]` resolves to one of three
> things, and the same page + nested post route serve all three — there is no separate folder
> route. Resolve in a **fixed order** so the shared namespace never collides:
>
> 1. `all` → posts from every followed feed, merged (the home header's target).
> 2. `saved` → all saved posts merged, or a **saved-group** uid (`saved_*`:
>    Bookmarks / Favorites / Later, defined in `app/utils/saved.ts`) → that group's posts.
> 3. a **folder** uid (`folder_*`) → the folder's merged stream (member feeds minus muted).
> 4. otherwise a **feed** uid (`feed_*`) → that feed's own posts.
>
> Ids are prefixed (`feed_*`, `folder_*`, `saved_*`, plus the literals `all` and `saved`) so
> resolution is unambiguous. **The API resolves the uid in this same order**
> (`GET /feeds/{uid}/posts`), so the page stays thin for real: `usePostList(uid)` pages the
> stream it's handed and the screen renders it — feed / folder / saved differences live in one
> place, on the server, not in template conditionals on either side.

---

## 0. Sign in — `pages/login.vue`

**Purpose:** the one screen a signed-out person can see. FeedMe is **login-only** — no guest
mode, no anonymous browsing ([backend.md](./backend.md#auth)) — so this is the gate in front of
every other screen.

**The user can:**
- **Sign in with Google** — the primary action, and in the finished app the only one.
- **Sign in with a dev token** — a second, temporary control below it, for accounts with no
  Google identity ([backend.md](./backend.md#auth)). Both ways in ship today; retiring this one is
  an owned follow-up ([backend-roadmap.md](./backend-roadmap.md) T8).
- Nothing else. There is no sign-up (the account is created by the first sign-in), no password
  recovery, and no way past this screen.

**Layout:** brand, one line of what the app is for, then the sign-in block — and nothing above it
depends on its size, because **Google owns the chrome inside its button** (theme, size, text and a
400px width cap are the whole surface; its frame paints its own background, which is why the app's
themes stop at the button's edge). The column is sized to that cap so both controls sit on the
same edges, and the two are separated by **spacing alone** — no divider, per
[design-system.md](./design-system.md). The screen renders **without the app layout**, so the
desktop shell never appears around it.

**Feedback:** a rejected sign-in says so on this screen (the credential is proved before it's
kept), rather than letting the user through into a redirect loop — **one message per control**, so
a failure is never reported under the control that didn't fail. A refused sign-in never counts as
a dead session: an existing one survives it untouched.

**Data:** `POST /auth/google` — trades Google's credential for our bearer token — and `GET /me`,
the profile that proves whichever token was set. Nothing else on this screen calls the API, and no
other screen loads anything until this one has been passed.

**Flow:**
- Signed out, any route → `/login`. After signing in → the feeds list (`/`).
- Already signed in, `/login` → the feeds list. The session survives reloads.
- **Sign out** (Settings → Account) or a **session the server no longer accepts** → back here,
  with the app's data cleared, so the next person to sign in never sees the last one's feeds.

---

## 1. Feeds list — `pages/index.vue`

**Purpose:** the home screen. Shows the pinned **Saved** group, the user's **folders**, and any
**loose** feeds (feeds not in a folder). Folders only exist here — they are created, read, and
edited from this screen. A **FEEDME** wordmark leads the list, then **Home** is an ordinary list
row like the rest (same height and surface, an inline **All feeds** caption) — tapping it opens
the merged read of every followed feed (`/feed/all`) — with the options 3-dot trailing where
folder rows keep their chevron.

**List order:** pinned **Saved** group → **folders** → **loose feeds**.

**The user can:**
- See a pinned **Saved** row → tapping it lists all posts the user has saved (`/feed/saved`);
  expanding its chevron reveals the three saved groups — **Bookmarks / Favorites / Later**
  (`/feed/saved_*`), so saves can be organized instead of landing in one pile.
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

**Data:** one `GET /home` round-trip — the account's `feeds`, `folders`, the shared top-level
order, and the per-group saved counts the Saved rows show. A feed is **loose** when its `uid` is
in no folder's `feed_uids`.

**Navbar:** `components/Navbar.vue` provides the menu (`→ /settings`) and the **+** create menu
via `components/IconButton.vue`.

**Empty state:** if the user follows nothing yet (no feeds, no folders), the list is replaced
by a first-run nudge — an explainer and a primary **Add your first feed** action into the Add
flow. If the home request **failed** instead, the same space says the server couldn't be
reached and offers **Try again** — an unreachable app must never be mistaken for an empty
account. Neither appears while the request is still in flight.

**Desktop:** this same list renders in the sidebar, persistent beside the posts/post panes
(not behind a drawer) — see the Routing note.

---

## 2. Feed page — `pages/feed/[uid].vue` (currently `Feed.vue`)

**Purpose:** show a post list for the selected `uid`. This is the **master** pane; on desktop
the selected post renders beside it in its own pane (detail), on mobile it's full-screen. The
page is **polymorphic** — `uid` is a real feed, `saved`, or a folder (see screens 1 and 6, and
the Routing note's resolution order). The render is identical; only the post list it resolves
differs.

**The user can:**
- See a scrollable list of **PostCards** (`components/PostCard.vue`) for this feed, which
  **keeps loading as they scroll** — there is no "load more" button and no page count.
- **Tap a post** → open the Post page (`/feed/[uid]/post/[postUid]`).
- Go **back** → Feeds list.

**Data:** `GET /feeds/{uid}/posts`, cursor-paged — the same polymorphic `uid` resolved
server-side in the order below, so the screen renders the stream it is given rather than
filtering one. Posts are newest-first by `published_at`, except the saved lists, which are
newest-**save** first. When `uid` is `saved`, the list is every saved `Post`; when `uid` is a
**folder**, the list is its member feeds' posts merged (minus muted) — see screen 6.

**When there's nothing to show:** an empty stream says so plainly ("No posts here yet"); a
failed page says the posts couldn't be loaded and stops asking, rather than retrying into a
server that just refused.

**PostCard** shows: `image_url`, `title`, and `published_at` (and a type cue from the parent
feed). Tapping it opens the Post page.

**Desktop:** the posts pane is fixed-width and always visible beside the post pane; there is
no back navigation for it (nothing to go back to — the sidebar is always there instead).

---

## 3. Post page — `pages/feed/[uid]/post/[postUid].vue` (currently `[Post].vue`)

**Purpose:** read a single post in full. Nested under the feed, so it's the **detail** pane —
it renders beside the feed list on desktop and full-screen on mobile.

**The user can:**
- Read the post: `title`, `image_url`, formatted `published_at`, and its text. The **article
  text** is the goal; until it can be extracted, the screen shows what RSS gave us (`summary`)
  as plain text — a summary is untrusted third-party markup and is never rendered as HTML.
- **Save** the post (toggle) — it lands in **Bookmarks**; toggling again unsaves it. See
  [data-model.md](./data-model.md#saved-state).
- **Open source** — opens `post.post_url` (the original article / YouTube watch page) in a
  new tab.
- Go **back** → the Feed page (the `[uid]` it was opened from — a real feed, or `saved`).

**Data:** `GET /posts/{uid}` for the post named by `postUid`; the route `uid` is the feed
context it was opened in.

**Desktop:** until a post is tapped, the post pane shows a placeholder ("Select a post")
instead of this screen — there is no auto-selected first or last-read post.

---

## 4. Add feed — `components/add/Drawer.vue` (bottom drawer, three-phase wizard)

**Purpose:** subscribe to a new feed. Reached from the navbar **+** (opens `/add` directly).
The drawer is hosted in the layout and mirrors the settings drawer: `/add` renders the home
component behind the sheet (`pages:extend` hook), and closing routes back to `/`. Inside the
sheet it's an **in-drawer wizard** — three phases that slide right/left (matching the house
`page-slide`/`panel-slide` transitions) with a back button, all state in `useAddFeedWizard()`.

**Phase 1 — pick a type.** A vertical list of source types: **Website**, **YouTube**, **Reddit**
(podcasts later). Tapping one advances to phase 2. Reddit's account-connect step is deferred
(see [`pending_tasks/reddit-connect.md`](../pending_tasks/reddit-connect.md)); for now it behaves
like the others.

**Phase 2 — paste or search.** Header shows the chosen type + a back button. One input
("Paste a link or search…") does double duty: paste a link *or* search a keyword. While empty it
shows a **Paste** chip (reads the clipboard on tap — browsers block silent reads). Submit → a
~1s loading skeleton → a short **results list** (title + site, no leading type icon since the type
is in the header), each with an add `+`.

**Phase 3 — choose destination.** Tapping a result's `+` advances here. Header is "Add to" + a
back button. It reuses the home feed list: a **Feeds (top level)** row plus one row per **folder**.
Tapping a destination **commits** — the feed is subscribed there, the drawer closes, and the home
list reflects it. Subscribing is the first step that can be **refused**: the sheet stays open
with the server's reason on it (a URL that turns out not to be a feed, or one already followed),
shown above the destination list where a long list can't push it out of reach, and only closes
once the subscribe lands. Run **scoped to a folder** (from screen 7's *Add feed*), the wizard
skips this phase — the destination is already known — and commits, and reports the same
refusal, from the paste/search step.

**Scope:** one feed → one destination per pass (multi-select / multi-folder deferred; the data
model stays many-to-many, so a feed can join more folders later via a folder's *Edit feeds*).

**Data:** candidates come from `GET /discover?type=&q=`, which **isn't built yet** (T11). Until
it lands the step resolves one case without a server — a pasted **feed** URL becomes a single
candidate, which is all `POST /feeds` needs — and says it found nothing for anything else (a
keyword, a YouTube handle, a bare subreddit name). Committing calls `POST /feeds`
(`{feed_url, folder_uid?}`) through `useFeedsStore().addFeed()`; the server finds-or-creates the
shared source, fetches it, and answers with the feed's real name.

**Components:** `add/Drawer.vue` (mobile sheet host: open protocol + commit/close/reset),
`add/Steps.vue` (the phase switch itself — reused by the desktop presentation below),
`add/TypeStep.vue`, `add/SearchStep.vue`, `add/DestinationStep.vue`, and the `useAddFeedWizard()`
composable. **Not yet built:** real search / RSS discovery, live metadata (sub counts, latest items),
and form validation via the installed **VeeValidate + Zod** stack.

**Desktop:** `/add` presents as a single-pane content area sliding in over the two reading panes
(sidebar stays usable) instead of a bottom sheet — there is no master beside it, since the wizard
is linear steps with nothing to list; the wizard itself is unchanged. Settings and folder editing,
by contrast, split the same content area into a master–detail pair (screens 5 and 7); editing a
loose feed is single-pane like this one.

---

## 5. Settings — `/settings/:panel?` (drawer on mobile, master–detail pane on desktop)

**Purpose:** account, appearance, app info, and support. Same master/detail shape as feeds: the
settings nav (the section list) is the **master**, the chosen subpage is the **detail**. On
mobile both live as panels inside one bottom sheet (`components/settings/Drawer.vue`) that
slide between each other; there are no separate settings page files — every `/settings/*` path
renders the home page's component behind the sheet (see the Routing note) and the sheet swaps
its panel by path. On desktop the section list and the open subpage render side by side, in the
same 40/60 master–detail split the reader uses for its posts/post panes — `/settings` alone
shows the list with a "Select a section" placeholder on the right. The sidebar carries a single
**Settings** link, not a second copy of the section list.

**Subpages:**
- **Account** — `/settings/account` — how you're signed in, member since, and **Sign out**
  (which ends the session server-side and returns to screen 0).
- **Appearance** — `/settings/appearance` — card style, font size, theme (see
  [product-overview.md → Planned](./product-overview.md#planned-not-now)).
- **About** — `/settings/about` — app info.
- **Report an issue** — `/settings/report`.

**The user can:**
- Open any subpage from the settings nav; navigate between them with panel-slide transitions
  (mobile) or an instant swap in the detail pane (desktop — only the content area's own
  open/close slides, see [current-state.md](./current-state.md)).
- Go **back** → closes Settings, returning to wherever it was opened from (mobile) / slides back
  out to the frozen reading position (desktop).

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

**Desktop:** renders through the same posts pane as screen 2 — no separate treatment.

---

## 7. Create & edit folders / feeds (from the home list)

**Create — navbar `+`:**
- **New feed** → the **+** opens the Add drawer at `/add` directly (screen 4).
- **New folder** → a route-backed drawer/page: enter a **name** and **pick member feeds**
  (multi-select from existing feeds). Confirm → the folder appears in the Feeds list. Same
  drawer-on-mobile / panel-on-desktop pattern as Add feed. **Entry point is undecided** — the
  old **+** menu that offered both was dropped; where folder creation is triggered from is a
  later design decision.

**Edit — context menu** (long-press on mobile; 3-dot / overflow on desktop). Built as a
route-driven **edit drawer** (`app/components/edit/Drawer.vue`, `/edit/*`) rather than a popover
menu: long-press (or a desktop hover 3-dot) on a folder opens the **folder panel** (rename,
per-feed mute toggles, add a feed, delete the folder), and tapping a member feed — or
long-pressing a loose feed — opens the **feed panel** (`/edit/:uid/feed/:feedUid`): rename it,
with its RSS URL shown as read-only context, and remove or delete. The destructive buttons are
labelled with the three actions below, word for word, and a `Source` is never named on screen
([backend.md](./backend.md) § Vocabulary). On desktop this presents in the content area (see the
Routing note) instead of a bottom sheet: a folder's panel is the **master** pane and the open
member's feed panel — or the scoped add steps, or a delete confirm — is the **detail** pane
beside it, with a "Select a feed" placeholder until one is open (the same master–detail split as
Settings, screen 5, and the reader). Editing a **loose** feed has no list beside it, so it takes
the content area single-pane instead — like Add (screen 4) — rather than leaving a dead pane
beside a squeezed form. An `/edit/*` route never shows an empty panel: the
drawer waits for the account's data before opening, and a uid it then can't find — a stale link,
a folder deleted on another device — sends the reader home.

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

**Destructive cascade** (mirrors [data-model.md](./data-model.md#cascade-rules)). All three
actions confirm before committing:
- **Remove from folder** — unlinks one membership; feed stays subscribed.
- **Delete feed** — unsubscribes the feed everywhere (all folders + the list).
- **Delete folder** — removes the folder **and unsubscribes its member feeds**, *except* any
  member that also belongs to another folder; the confirmation **names how many feeds will be
  unsubscribed**.

---

## Cross-screen behaviors

- **Back navigation** follows the route nesting: Post → Feed → Feeds list (where "Feed" is the
  `/feed/[uid]` it opened from — a real feed, `saved`, or a folder), and Settings subpage →
  Settings → wherever it opened from. Add / Edit close back to `/` on mobile, or to the frozen
  reading position on desktop (see the Routing note).
- **Master/detail by viewport:** the same routes present as one pane on mobile (nested
  `<NuxtPage/>`s, sliding like a stack) and three panes on desktop (sidebar + posts pane + post
  pane, composed by the layout directly from the route and the stores — not by rendering
  `<NuxtPage/>` — see the Routing note above). Layout is a presentation concern; the routes and
  `pages:extend` records don't change.
- **Type-aware rendering:** `Feed.type` drives small differences (YouTube thumbnail vs.
  article body), but the layout and interactions are the same across types.
- **Signed out is a state, not an error:** every route redirects to screen 0 without one, and a
  session the server stops accepting drops the user there mid-use with the app's data cleared.
  An **unreachable server** is different and is never confused with it — the app stays on its
  feet and says the data couldn't be loaded (screen 1).
