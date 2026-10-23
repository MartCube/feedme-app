# Screens & Flows

This is the core spec: every screen, its purpose, what the user can do there, and where it
navigates. File references point at `app/pages/` and `app/components/`.

## Navigation map

```
                    ┌──────────────────────────┐
                    │  Feeds list  (index.vue) │
                    │  Home · Saved · feeds    │
                    └───┬──────────┬───────┬───┘
        tap a feed      │          │       │   navbar
                        ▼          │       └─► +  → Add drawer (add a source)
        ┌───────────────────────┐  │                type → search → "Add to" a feed
        │  Post list  (master)  │  │                or New feed
        │  /feed/[uid]          │  └──────────► Settings (/settings/:panel?)
        │  list of PostCards    │                /settings/{account, appearance,
        └───┬───────────────┬───┘                          about, report}
   tap the  │               │  tap a post
   title    ▼               ▼
  ┌───────────────────┐  ┌──────────────────────────────┐
  │  Feed page        │  │  Post page  (detail)         │
  │  /feed/[uid]/info │  │  /feed/[uid]/post/[postUid]  │
  │  sources, on/off  │  │  full readable post          │
  └─────────┬─────────┘  └──────────────────────────────┘
            │ pencil · tap a source          actions: Copy link · Open source · Save
            ▼
     edit feed · a source's page · confirms        (/feed/[uid]/info/…)

   uid can be 'all' → every source that's on in some feed, merged; 'saved' → the Saved
   feed; or a feed uid → that feed's enabled sources, merged.
   Desktop: sidebar + posts pane + post pane side by side; the post pane shows the feed
   page until a post is open. See screens 1, 2, 3 and 6.

   Signed out, every route above redirects to /login (screen 0) — there is no
   anonymous surface. Signing out, or a session going stale mid-use, lands there too.
```

> **Routing.** Posts nest under feeds and Settings subpages nest under Settings, so the route
> *is* the navigation context — but that context now drives **two different renderers**
> instead of one nested-page tree:
>
> - **Mobile** (< 1024px): each route is its own page, and `feed/[uid].vue` is a bare
>   `<NuxtPage/>` passthrough to its `index.vue` / `post/[postUid].vue` / `info/[...rest].vue`
>   children — one pane at a time, sliding like a navigation stack.
> - **Desktop** (≥ 1024px): `app/layouts/default.vue` renders `DesktopShell` instead of
>   `<NuxtPage/>` at all. The shell reads the live route (`useRouter().currentRoute`, since
>   Nuxt's `useRoute()` only resyncs when a `<NuxtPage/>` resolves and the shell renders none)
>   and composes three columns directly from it and the `feeds`/`settings` stores: a sidebar
>   (pinned Home / Saved / New Feed rows, a foldable **Feeds** group, a foldable **Settings**
>   group listing the settings sections), a posts pane, and a post pane.
>   Settings/Add open inside the post pane instead of a drawer, over the reader and beside the
>   posts list (no slide — nothing on desktop animates, see [current-state.md](./current-state.md)
>   § Resolved decisions → Desktop motion); a section or step replaces the pane, as on a phone. The post pane shows the
>   feed page (screen 6) whenever no post is open. The sidebar's wordmark, the posts pane's
>   title/search row, and the post pane's actions row each stay pinned to the top of their own
>   column, reachable while that column scrolls beneath them. **The routes and
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
>     [uid].vue                → mobile: <NuxtPage/> passthrough;  uid: feed | 'all' | 'saved' | saved_*
>     [uid]/
>       index.vue              → /feed/[uid]              (post list)
>       post/[postUid].vue     → /feed/[uid]/post/[postUid]  (post)
>       info/[...rest].vue     → /feed/[uid]/info and everything under it: the feed page, its
>                                edit form and delete confirm, a source's page and its remove
>                                confirm — one catch-all record, the tail picks the view
>                                (utils/feed-info.ts)
>
> pages:extend (nuxt.config.ts) adds these paths, all rendering the SAME index.vue component
> (the home page, kept mounted behind a drawer on mobile / beside the post pane's
> content on desktop) — there are no separate settings.vue / settings/*.vue page files:
>   /settings/:panel?          → SettingsDrawer (mobile) / post pane (desktop)
>   /add                       → AddDrawer (mobile) / post pane (desktop)
> ```
>
> **The post list is polymorphic.** Its `[uid]` resolves to one of three things, and the same
> page + nested post route serve all three — there is no separate route for a group of sources.
> Resolve in a **fixed order** so the shared namespace never collides:
>
> 1. `all` → posts from every source that is on in at least one feed, merged (the home header's
>    target).
> 2. `saved` → all saved posts merged, or a **saved-group** uid (`saved_*`:
>    Bookmarks / Favorites / Later, API-only — the app does not link them) → that group's posts.
> 3. otherwise a **feed** uid (`feed_*`) → that feed's merged stream: its **enabled** sources,
>    newest first.
>
> Ids are prefixed (`feed_*`, `saved_*`, plus the literals `all` and `saved`) so
> resolution is unambiguous. **The API resolves the uid in this same order**
> (`GET /feeds/{uid}/posts`), so the page stays thin for real: `usePostList(uid)` pages the
> stream it's handed and the screen renders it — feed / saved differences live in one
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

**Purpose:** the home screen. Shows the pinned **Saved** row and the user's **feeds** — a flat
list, nothing nested: a feed is already a group of sources, so there is nothing to expand. A
**FeedMe** wordmark leads the list (the mark itself is a link to `/feed/all`), then **Home** is
an ordinary list row like the rest (same height and surface, just the name) —
tapping it opens the merged read of every source that's on in some feed (`/feed/all`).

**List order:** **Home** → pinned **Saved** → **feeds**, in the order `GET /home` returns them.

**The user can:**
- See a pinned **Saved** row, with the total number of saved posts beside it (once there are
  any) → tapping it lists
  all posts the user has saved (`/feed/saved`). The app shows one Saved list — no groups — and Saved has no feed page of its own
  (see screen 6).
- See each **feed** as a row: its name, and a count of its sources beside it when it holds
  anything but exactly one (so a multi-source or empty feed shows its count, a one-source feed
  is just its name) → **tap** → read it (`/feed/[uid]`, screen 2).
- **Add** via the navbar **+**: it opens the **Add drawer** directly (`→ /add`) — a new source,
  into an existing feed or a New feed (screen 4).
- Tap the **menu** icon (navbar) → open the Settings drawer.

Everything done *to* a feed or its sources — rename, description, switching a source on or off,
removing, deleting — lives on the feed page (screen 6), reached from the feed's own post list.
The list itself has no overflow buttons, no long-press and no options sheet.

**Data:** one `GET /home` round-trip — the account's `feeds` (each with its description and its
sources) and the per-group saved counts the Saved row shows.

**Navbar:** `components/Navbar.vue` provides the menu (`→ /settings`) and the **+** (`→ /add`)
via `components/ui/IconButton.vue`.

**Empty state:** if the user follows nothing yet (no feeds), the list is replaced
by a first-run nudge — an explainer and a primary **Add your first feed** action into the Add
flow. If the home request **failed** instead, the same space says the server couldn't be
reached and offers **Try again** — an unreachable app must never be mistaken for an empty
account. Neither appears while the request is still in flight.

**Desktop:** this same list renders in the sidebar, persistent beside the posts/post panes
(not behind a drawer); the wordmark leading it stays pinned to the top of the sidebar while
the list scrolls beneath it — see the Routing note. The sidebar has three groups: the
**pinned rows** (Home, Saved, **New Feed** → `/add`), the **Feeds** group, and the **Settings**
group, which lists the settings sections directly so one click opens one. Feeds and Settings
fold under a caption header with a caret (200ms); the open/closed state is remembered on the
device, not the account. Settings → Appearance → *Sidebar icons* (desktop only, on the device
too) shows or hides an icon beside the fixed rows — Home, Saved, New Feed and the settings
sections; feeds never carry one.

---

## 2. Post list — `pages/feed/[uid]/index.vue`

**Purpose:** show a post list for the selected `uid`. This is the **master** pane; on desktop
the selected post renders beside it in its own pane (detail), on mobile it's full-screen. The
page is **polymorphic** — `uid` is a feed, `all` or `saved` (see the Routing note's resolution
order). The render is identical; only the post list it resolves differs. (A feed's own page —
its description and sources — is a different screen, number 6, reached from this one's title.)

**The user can:**
- See a scrollable list of **PostCards** (`components/PostCard.vue`) for this feed, which
  **keeps loading as they scroll** — there is no "load more" button and no page count.
- **Tap the info icon** (an "i" right after the title) → the feed's own page (screen 6). On
  a phone it is a page of its own (`/feed/[uid]/info`), pushed with the page slide and
  dismissed with swipe-back; on desktop the feed page already fills the post pane while no
  post is open, so the icon just links to `/feed/[uid]` — which closes the open post. The
  title itself is plain text: a visible icon instead of a hidden tap target _(2026-10-08)_.
  **Home** and **Saved** have no page of their own, so they have no icon.
- **Search** this list: a magnifying glass on the title row swaps the title for a search box
  ("Search *{this list's name}*"), and the list narrows **as they type** to the posts in this
  same `uid` that match — a partial word is enough, newest first. Results page like the list
  does. The search is part of the URL (`?q=`), so a reload, a shared link and **back from a
  post** all return to the same results; the X on the row — or **Escape** in the box
  _(2026-10-09)_, or leaving for another list — clears it and closes the box. Same row on both viewports — the desktop posts pane has no navbar, so the entry lives on
  the list itself.
- **Tap a post** → open the Post page (`/feed/[uid]/post/[postUid]`).
- Go **back** → Feeds list.

**Data:** `GET /feeds/{uid}/posts`, cursor-paged — the same polymorphic `uid` resolved
server-side in the order below, so the screen renders the stream it is given rather than
filtering one. Posts are newest-first by `published_at`, except the saved lists, which are
newest-**save** first. When `uid` is `saved`, the list is every saved `Post`; when `uid` is a
**feed**, the list is its enabled sources' posts merged, so switching a source on or off on the
feed page changes what this list holds — it reloads as soon as the write has landed. With a
query, `GET /search?q=&scope={uid}` instead — the same page shape and cursor, so searching is a
different URL and nothing else ([backend.md](./backend.md#search)).

**When there's nothing to show:** an empty stream says so plainly ("No posts here yet"), and an
empty search says which query matched nothing; a failed page says the posts couldn't be loaded
and stops asking, rather than retrying into a server that just refused.

**PostCard** comes in **two versions**, chosen in Settings → Appearance → *Post cards*: **Image**
(default) — a square thumbnail beside the text: a meta row (a type icon and the source's name,
linking to its `site_url` and always underlined, then `·` and `published_at`), the `title`, and a
three-line excerpt of the `summary` — and **Compact** — the date and title alone. The title link
covers the whole card; the source link sits above it. A post with no image is compact under either
setting, and an image that fails to load collapses the card to compact rather than leaving a
broken box. The image is the API's `post.image` (a proxied, resized `src`/`srcset` —
[images.md](./images.md)); tapping the card opens the Post page. A card rests on the elevated
surface; the selected card — and, on desktop, the hovered one — steps up to the muted surface
(see [design-system.md](./design-system.md) § Color roles → Hover state).

**Desktop:** the posts pane is always visible (50% by default; 60% or 40% per Settings → Appearance → *Reading panes*) beside the post pane; there is
no back navigation for it (nothing to go back to — the sidebar is always there instead). Its
title/search row stays pinned to the top of the pane while the list scrolls beneath it — see
the Routing note.

**Desktop keyboard** _(2026-10-21)_: **Esc** closes the top layer, one per press — Settings/Add
(back to the frozen reading position), a feed-page sub-view (to where its own back goes), an open
post (to its feed page, keeping the search); on the bare feed page it does nothing. The search box
keeps its own Esc (close and clear). **/** opens and focuses the search; **Enter** in it blurs
("done typing"). **↓/↑** step the open post through the list (↓ with none open opens the first;
the first open is a history push, later steps replace, so Back leaves the feed) and the pane
scrolls to follow. Arrows are inactive in an input and while Settings/Add is open. The full list
is Settings → Keyboard shortcuts.

---

## 3. Post page — `pages/feed/[uid]/post/[postUid].vue` (currently `[Post].vue`)

**Purpose:** read a single post in full. Nested under the feed, so it's the **detail** pane —
it renders beside the feed list on desktop and full-screen on mobile.

**The user can:**
- Read the post, top to bottom: the `title`; the same **meta row** the card has (the source's
  name, linking to its `site_url`, then `·` and the formatted `published_at` — the source is
  named even after it has left every feed, since the post carries it); a 16:9 **hero** (`post.image`, never enlarged past its own width;
  absent when the post has none or it fails to load — [images.md](./images.md) § Rendering) —
  or, for a YouTube post, the **video player** in its place (a Short gets a tall 9:16 box), with
  the description's line breaks kept and no inline **Open source** (the action bar has it); and
  the text. The **article text** — extracted and sanitised server-side — is the one text
  field the screen renders as markup; when extraction can't produce one the screen falls back to
  what RSS gave us (`summary`) as plain text — untrusted third-party markup, never rendered as
  HTML — plus **Open source**.
- **Copy link** — copies `post.post_url` (the original article / YouTube watch page, not a
  FeedMe link — opening one of those needs an account) to the clipboard.
- **Open source** — opens `post.post_url` in a new tab.
- **Save** the post (toggle) — it lands in **Bookmarks**; toggling again unsaves it. See
  [data-model.md](./data-model.md#saved-state).
- Go **back** → the post list (the `[uid]` it was opened from — a feed, `all` or `saved` —
  and, if it was opened from search results, those same results).

**Data:** `GET /posts/{uid}` for the post named by `postUid`, and `GET /posts/{uid}/article` for
the article text (`status: ok | unavailable` — `unavailable` is the fallback above, not an
error); the route `uid` is the feed context it was opened in.

**Desktop:** until a post is tapped, the post pane shows the feed page (screen 6) instead of
this screen — or, on **Home** and **Saved**, which have no page of their own, a placeholder ("Select a
post"). There is no auto-selected first or last-read post. The actions row (Copy link · Open
source · Save) stays pinned to the top of the pane the same way, on the side Settings →
Appearance → *Post actions* picks, and stays up from one post to the next while the new one
loads (hidden only if that post failed to load) — see the Routing note.

---

## 4. Add feed — `components/add/Drawer.vue` (bottom drawer, four-step wizard)

**Purpose:** add a source — and say which feed it goes into, or start a new one. Reached from
the navbar **+** (opens `/add` directly), or from a feed's own page (screen 6) already pointed
at that feed. The drawer is hosted in the layout and mirrors the settings drawer: `/add`
renders the home component behind the sheet (`pages:extend` hook), and closing routes back to
`/`. Inside the sheet it's an **in-drawer wizard** — phases that slide right/left (matching the
house `page-slide`/`panel-slide` transitions) with a back button, all state in
`useAddFeedWizard()`.

**Phase 1 — pick a type.** A vertical list of source types: **Website**, **YouTube**, **Reddit**
(podcasts later). Tapping one advances to phase 2. Reddit's account-connect step is deferred
(see [`pending_tasks/reddit-connect.md`](../pending_tasks/reddit-connect.md)); for now it behaves
like the others.

**Phase 2 — paste or search.** Header shows the chosen type + a back button. One input
("Paste a link or search…") does double duty: paste a link *or* search a keyword. While empty it
shows a **Paste** chip (reads the clipboard on tap — browsers block silent reads). Submit → a
loading skeleton while `/discover` answers → a short **results list** (name + its **feed URL**,
which is what tells two feeds off one page apart; a YouTube channel leads with its avatar, and
there is no type icon since the type is in the header), each a multi-select card. A result
that is already in one of the user's feeds stays pickable — a source can sit in several — and
carries an **"In your feeds ·"** caption before its feed URL. A **YouTube search hit** is
captioned with its **subscriber count** instead ("61.4K subscribers · In your feeds"), and
every result has an **open-in-new-tab icon** linking its channel or site, so it can be judged
before it's picked _(2026-10-08)_. The select button stretches over the card and the link sits
above it — the post card's pattern, since a link can't live inside a button.

**Phase 3 — choose destination.** The forward button advances here. A quiet "Adding" list of
the picked sources, then **Add to**: a **New feed** card first (always there, and the common
case for a first source), then one card per existing feed with its source count. Tapping a
feed **commits** — every picked source joins it, the drawer closes, and the home list reflects
it. **New feed** advances to phase 4.

**Phase 4 — name the new feed.** A name input, prefilled with the first picked source's name
(so a one-source feed costs one tap); submitting creates the feed holding the picks and closes
the drawer. With several picks the feed is created with the first, then the rest are added to
it. The feed's description starts as that first source's own, and is edited later on the feed
page.

Adding is the first step that can be **refused**: the sheet stays open with the server's reason
on it (a URL that turns out not to be a feed — which leaves no empty feed behind — or a source
already in that feed), shown above the destination list where a long list can't push it out of
reach, and only closes once the add lands. If several picks are going in and one is refused,
the ones already in stay in.

**Pointed at a feed.** Opened from a feed's page with *Add source* (screen 6), the wizard
already knows its destination: it skips phases 3 and 4 and commits from the paste/search step,
reporting the same refusals there.

**Scope:** several sources → one destination per pass. Putting one source into a second feed is
a second pass — it stays pickable for exactly that.

**Data:** candidates come from `GET /discover?type=&q=` _(T11a, 2026-09-06)_. A pasted URL of any
shape resolves — a blog homepage or a post page, a YouTube channel URL or `@handle`, a subreddit
URL or a bare name — whether or not it is the feed URL itself; a page that declares no feed sends
the resolver up its own path and then to the usual `/feed`, `/rss.xml` guesses. Candidates
already in one of the user's feeds come back flagged `already_subscribed` (the caption above).
A **keyword under the YouTube card** searches
YouTube by channel name _(T11b, 2026-09-11)_ — up to five channels with their avatars; if YouTube
won't answer (quota spent), the step shows that as an error rather than an empty result. A
keyword under Website or Reddit still finds nothing (T11c, T11d).
Committing a New feed calls `POST /feeds` (`{name, feed_url}`) through `useFeedsStore().addFeed()`,
and every other source `POST /feeds/{uid}/sources` through `addSource()`; the server
finds-or-creates the shared source, fetches it, and answers with the whole feed.

**Components:** `add/Drawer.vue` (mobile sheet host: open protocol + commit/close/reset),
`add/Steps.vue` (the phase switch itself — reused by the desktop presentation below),
`add/TypeStep.vue`, `add/SearchStep.vue`, `add/DestinationStep.vue`, `add/NewFeedStep.vue`, and
the `useAddFeedWizard()` composable. **Not yet built:** keyword search for subreddits and our own
catalog (T11c, T11d), a candidate's latest posts before adding it (T14, `GET /discover/posts` —
planned), sub counts, and form validation via the installed **VeeValidate + Zod** stack.

**Desktop:** `/add` opens inside the post pane _(2026-10-13)_ instead of a bottom sheet; the
sidebar and the posts list stay usable beside it, and the reader underneath stays as it was.
The wizard is unchanged except that its steps cut rather than slide there.

**Enter** submits the new-feed name. **When it finishes**, the app opens the feed the source
landed in and selects it (on a phone the sheet closes first).

---

## 5. Settings — `/settings/:panel?` (drawer on mobile, post pane on desktop)

**Purpose:** account, appearance, app info, and support. Same master/detail shape as feeds: the
settings nav (the section list) is the **master**, the chosen subpage is the **detail**. On
mobile both live as panels inside one bottom sheet (`components/settings/Drawer.vue`) that
slide between each other; there are no separate settings page files — every `/settings/*` path
renders the home page's component behind the sheet (see the Routing note) and the sheet swaps
its panel by path. On desktop it opens inside the post pane _(2026-10-13; was two panes over the whole reading
area)_, beside the posts list: `/settings` shows the section list, and a section **replaces**
it with the panel's own back button returning — the phone's stack without the slide — held to
the form measure, since a form has a natural width. The
sidebar lists the sections itself (its Settings group), so on desktop a section opens in one
click and the panel's top button is a **close** (back to the reading position), not a back
to a section list.

**Subpages:**
- **Account** — `/settings/account` — how you're signed in, member since, and **Sign out**
  (which ends the session server-side and returns to screen 0).
- **Appearance** — `/settings/appearance` — theme,
  **Post cards** (Image / Compact, T15a — [images.md](./images.md) § Rendering), **Post
  actions** _(2026-10-13)_ (Copy link, Open source and Save sit on the **left**, the default, or
  the **right** of the post's action row — the phone's post navbar and the desktop pane strip
  both follow; stored on this device only for now, not in the account), and on desktop
  **Reading panes** (posts wider 60/40, equal 50/50, post wider 40/60); font size is
  still planned (see [product-overview.md → Planned](./product-overview.md#planned-not-now)).
- **Keyboard shortcuts** _(2026-10-21)_ — `/settings/shortcuts`, desktop only (hidden from the
  phone's section list) — a static reference of the shortcuts, grouped Reading / Search / Anywhere.
- **About** — `/settings/about` — app info.
- **Report an issue** — `/settings/report`.

**The user can:**
- Open any subpage from the settings nav; navigate between them with panel-slide transitions
  (mobile) or an instant swap in the detail pane (desktop — nothing there slides, see
  [current-state.md](./current-state.md) § Resolved decisions → Desktop motion).
- Go **back** → closes Settings, returning to wherever it was opened from (mobile) / to the
  frozen reading position (desktop).

---

## 6. Feed page — `components/feed/Info.vue` (`/feed/[uid]/info`)

**Purpose:** what a feed *is* and what is in it — its name, its description and its sources —
and the way into every edit to them. A feed is a group of sources, and this is the page that
shows the group. It is reached by the info icon button beside the search in the title row above a feed's posts (screen 2; it gives way to the search box while search is open); the home
list has no menu for it.

**The user can:**
- Read the feed's **name** and **description** (the description is left out when empty).
- See its **Sources**, with a count of how many are on out of how many ("Sources 2/3"): one
  row per source in the feed's own order, showing the name the user knows it by — their
  rename in this feed, else the source's own title.
- **Switch a source on or off** with the toggle on its row — right there, immediately, with no
  Save. An off source stays in the feed and stays listed (dimmed), but is left out of this
  feed's posts, and out of All feeds unless another feed has it on. On/off belongs to this
  feed only.
- **Tap a source's name** → its page (screen 7).
- **Add source** (the dashed row below the list) → the add wizard (screen 4), already pointed
  at this feed.
- **Edit** (the pencil) → the name and description form (screen 7).
- **Delete** (the trash can) → the delete confirm (screen 7). Edit and Delete are separate icon
  buttons in the page's header; backing out of the confirm returns here.
- Go **back** → the post list (on desktop the list is already beside it, so the button keeps
  its space and hides).
- A feed with no sources says "No sources yet." and offers **Add source** all the same.

**Saved** and **Home** have no feed page (as of 2026-10-21). The backend still keeps
three saved groups (`/feed/saved_*` resolve), but the app does not surface them.

**Mobile:** `/feed/[uid]/info` is a page of its own. It pushes in with the page slide from the
post list and has swipe-back; so does each deeper view (screen 7), one level at a time — a
source's remove confirm goes back to the source, which goes back to the feed page, which goes
back to the posts.

**Desktop:** the post pane shows the feed page — or whichever of its deeper views is open —
whenever no post is. It replaces the "Select a post" placeholder on **Home** and **Saved**, which
have no page of their own and keep the placeholder. Opening a post replaces it; the list's title
links to `/feed/[uid]`, which closes the post and brings it back. The view is remembered with
the rest of the reading position, so opening Settings or Add over the reader and coming back
finds it as it was.

**A stale link** — a feed deleted on another device, or a source that has since left it — never
shows an empty panel: once the account's data has loaded, the reader is sent to the feed page,
or home if the feed itself is gone.

**Data:** none of its own. The feed and its sources come from the `GET /home` the home list
already holds, and every write on this page swaps the server's copy of the whole feed back in
([backend.md](./backend.md) § Endpoint catalog).

---

## 7. Create & edit feeds and sources (from the feed page)

Editing is not a drawer or a menu: each view is a deeper path under the feed page
(`/feed/[uid]/info/…`, screen 6), so it slides like the rest of the reader on a phone and fills
the post pane on desktop. They all render through one component, and Back from each goes to
the one above it.

**Create.** A feed is made in the add wizard (screen 4) — *New feed*, with its first source —
and a source is added to an existing feed either there (*Add to* that feed) or from the feed
page's *Add source*. There is no separate create screen.

**Edit feed** — `/feed/[uid]/info/edit`, from **Edit** on the feed page. A **Name** and a
**Description**, committed together by a **Save** pill (live once something changed and the
name is not empty). Save returns to the feed page. Delete is not on this form _(2026-10-13)_;
it is its own button on the feed page.

**Source page** — `/feed/[uid]/info/source/[sourceUid]`, from a source's row. The source's name,
"In {feed}" beneath it, then:
- **Name** — the user's own name for the source *in this feed*. The source's own title shows as
  the placeholder, and leaving it blank means that title.
- **Link** — the source's feed URL, editable. Changing it swaps the row to a *different*
  source: the new URL is fetched first, so one that isn't a feed (or is already in this feed)
  is refused with the reason under the field and nothing changes. The shared source behind the
  old link is never edited.
- **Save** — commits the name and the link, then returns to the feed page (a new link has to,
  since it is a different source with a different identity).
- **Remove from this feed** — see below.

**Destructive actions** (mirror [data-model.md](./data-model.md#cascade-rules)). Both go through
a confirm view, reached by a button that arms before routing and never mutates anything itself:
- **Remove from this feed** — `/feed/[uid]/info/source/[sourceUid]/remove`. Takes that one
  source out of the feed. It stays in every other feed that has it, saved posts stay, and the
  feed stays even if it ends up empty. Confirming returns to the feed page.
- **Delete feed** — `/feed/[uid]/info/delete`. Removes the feed and its placements. A source
  that no feed holds any more stops being polled; saved posts stay. Confirming returns home.

The buttons carry those two labels word for word. A **source** is named on screen here — it is
now part of the product's vocabulary ([backend.md](./backend.md) § Vocabulary).

---

## Cross-screen behaviors

- **Back navigation** follows the route nesting: Post → Post list → Feeds list (where "Post
  list" is the `/feed/[uid]` it opened from — a feed, `all` or `saved`); Feed page → Post list;
  Edit / Delete / a source's page → Feed page, and a source's remove confirm → that source's
  page (delete confirm → Feed page); and Settings subpage → Settings → wherever it opened from. Add
  closes back to `/` on mobile, or to the frozen reading position on desktop (see the Routing
  note).
- **Master/detail by viewport:** the same routes present as one pane on mobile (nested
  `<NuxtPage/>`s, sliding like a stack) and three panes on desktop (sidebar + posts pane + post
  pane, composed by the layout directly from the route and the stores — not by rendering
  `<NuxtPage/>` — see the Routing note above). Layout is a presentation concern; the routes and
  `pages:extend` records don't change.
- **Type-aware rendering:** `Source.type` drives small differences (YouTube thumbnail vs.
  article body), but the layout and interactions are the same across types.
- **Images are never hotlinked.** Every image on screen — post images, feed icons, the pictures
  inside an article — is a URL the API built through the image proxy; the frontend adds
  `sizes` and nothing else. The stages, sizes and fallbacks are [images.md](./images.md).
- **Signed out is a state, not an error:** every route redirects to screen 0 without one, and a
  session the server stops accepting drops the user there mid-use with the app's data cleared.
  An **unreachable server** is different and is never confused with it — the app stays on its
  feet and says the data couldn't be loaded (screen 1).
