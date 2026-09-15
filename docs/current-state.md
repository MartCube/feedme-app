# Current State

A snapshot of what's actually built vs. what the spec (these docs) describes. The goal is to
make the gap visible so implementation has a clear backlog. Update this as work lands.

_Last reviewed: 2026-09-15._

## Summary

The **design system** and **navigation/drawer UX** are well developed, and the three **reader
screens** (feeds list, feed page, post page) navigate end to end. **Desktop
(≥1024px) v1** now renders those same screens as a three-column shell — sidebar, posts pane,
post pane — composed by the layout from the same routes and store state; Settings/Add/Edit
present as a sliding content area over the reading panes instead of drawers — a master–detail
split where there's a list to sit beside, single-pane where there isn't. **The app runs on real
data** _(2026-09-01)_: a `/login` screen gates every route, and the account's own feeds,
folders, fetched posts, saved posts and settings all come from the Django API in `backend/`
(Django + django-ninja, Docker Compose) — the mock data files are deleted and nothing falls
back to them. **Writes are real too** _(2026-09-01)_: subscribing, renaming, folder membership,
mute and both deletes all go through the API, and the edit drawer's copy moved onto the spec's
nouns (folder / feed — no "source" on screen). **Sign-in is real** _(2026-09-03)_: `/login`
renders Google's own button and `POST /auth/google` trades its credential for our bearer token —
with the dev-token field deliberately kept beside it for now, so there are two ways in until the
dev path is retired. **Posts now age out** _(2026-09-07)_: a nightly job prunes unsaved posts
past 90 days and, per source, past the newest 500 — saved posts are exempt at any age — and
polling respects the same line, so a feed subscribed today arrives with only the posts inside
that window. **Posts are searchable** — `GET /search` _(2026-09-06)_ narrows any feed / folder /
saved list, and the feed page and the desktop posts pane search through it from a box on the
list's own title row. What has no endpoint behind it yet says so: the add wizard resolves any
**pasted URL** and searches **YouTube** by channel name, but a keyword under Website or Reddit
still finds nothing, and the home reorder has no UI. The gap runs the other way in **one** place:
`GET /posts/{uid}/article` extracts and caches article text as of _2026-09-05_, and **no screen
calls it yet**, so the reader still shows the RSS summary as plain text. See Resolved decisions →
Backend stack & API.
Backend work is sequenced in [backend-roadmap.md](./backend-roadmap.md), which tracks its
own status: **read that file's § Status for what to build next.**

## Built

- **Theme tokens** — 9 `--ui-*` color roles themed in `app/assets/css/themes.css` (two dark
  themes: Ink default + Claude; the old teal/ink/silver ramps are removed), plus the 4-size
  type scale (`text-title/subtitle/body/caption`, plus a brand-only `text-logo` for the wordmark
  — see [design-system.md](./design-system.md) § Type scale) and `shadow-elevated`. The same
  file defines a desktop-only `hover-accent` utility (the row's label goes `primary` on `:hover`,
  nothing else moves) used across list rows — see [design-system.md](./design-system.md) § Color
  roles → Hover state. The
  font family and type scale live in their own `app/assets/css/typography.css` (imported by
  `main.css`), and the
  6-step t-shirt spacing scale (`--spacing-2xs…xl` → `p-sm`, `gap-md`, `mt-lg`, …) in
  `app/assets/css/spacing.css`, alongside the `page-inset` utility every page/drawer
  wrapper uses for the screen inset (lg sides/top, xl bottom).
  See [design-system.md](./design-system.md).
- **Theme switch** — Settings → Appearance picks Ink or Claude via the persisted Pinia
  `settings` store (`pinia-plugin-persistedstate`, cookie — now a local cache in front of
  `GET`/`PUT /settings`, see **Data layer** below, which is what still paints the chosen theme
  server-side without a flash); `app.vue` applies `data-theme` on `<html>` via `useHead`.
- **Feed-list style switch** — Settings → Appearance → Feed list picks **List** (plain rows,
  default) or **Cards** (**top-level** home rows — Home, Saved, folders, loose feeds — become
  permanent `bg-elevated` + `shadow-elevated` cards, spaced `md` apart via per-row margins;
  member rows inside an expanded dropdown stay plain, spaced `xs`);
  `settings.feedListStyle`, persisted like the theme. In cards mode the top-level tap flash
  merges into the card surface — the icon accent flash stays the cue.
- **Scrollbar style switch** — Settings → Appearance → Scrollbar (desktop only, hidden on
  touch via `useIsDesktop()`) picks **Thin** (default), **Comfortable**, or **System** (native,
  writes no rules); `settings.scrollbarStyle`, persisted like the theme, applied as
  `data-scrollbar` on `<html>` from `app.vue` (same wiring as `data-theme`). Rules live in
  `app/assets/css/scrollbars.css` (thumb colors derived from `--ui-bg-muted` / a color-mix
  toward `--ui-text`, separate webkit and Firefox branches — the two must never target the
  same element or Chromium 121+ drops the webkit rules). Scroll containers across
  add/edit/settings/desktop components use the `scroll-host` utility this defines (an
  `overflow-y-auto` + reserved `scrollbar-gutter` pair) in place of plain `overflow-y-auto`.
- **Navbar** — `app/components/Navbar.vue` (menu → `/settings`, add → `/add`).
- **IconButton** — `app/components/ui/IconButton.vue` (round soft-fill button, accent press
  flash). A `quiet` variant blends into the page bg at rest and lifts to the normal
  elevated look while the press flash runs (home 3-dot options trigger).
- **Settings drawer** — `app/components/settings/Drawer.vue` hosts the sheet; the
  `/settings/:panel?` route renders the home component (via `pages:extend`) so the feed list
  stays behind the sheet on mobile, and panels swap as in-drawer components with `panel-slide`
  transitions. Main page (`settings/Home.vue`): in-flow close → title → section list with the
  shared tap-selection flash (row + leading icon accent flash). Subpages (Account / Appearance
  / About / Report) share `settings/Page.vue`: back + the section's own muted icon + `text-subtitle`
  title as a where-am-I cue (sections defined once in `app/utils/settings-drawer.ts`, exported as
  `settingsSections` and reused by the desktop sidebar). Both `settings/Page.vue` and the route
  map that picks a panel per path read `useRouter().currentRoute` rather than Nuxt's `useRoute()`
  so they stay correct when rendered inside the desktop content overlay (see Desktop shell v1,
  below). Appearance and Account are functional (theme/list/scrollbar switches; real profile +
  Sign out — see **Auth & login** below); About is static info (hardcoded version string) and
  Report is still a mock panel.
- **Add-feed wizard** — `app/components/add/Drawer.vue` hosts the sheet, like the settings
  drawer. The `/add` URL renders the home component (via the `pages:extend` hook) so the feed
  list stays behind the sheet on mobile; the navbar **+** links straight to `/add` (no dropdown),
  and close routes back to `/`. The four-phase slide switch itself lives in
  `app/components/add/Steps.vue` (`AddSteps`, emits `close`/`done` — the host decides what those
  mean, which is what lets the desktop content overlay reuse it), state in
  `useAddFeedWizard()`: **pick type** (`add/TypeStep.vue`, cards with an accent caret tap flash) →
  **paste/search** with a Paste chip, a loading skeleton (kept for the real search; nothing is
  in flight today), and results as **multi-select cards**
  (whole card toggles a trailing page-bg circle "well" that gains an accent checkmark when
  picked; a header forward button at IconButton size — disabled until ≥1 picked, accent when
  enabled — advances) (`add/SearchStep.vue`) → **choose destination** — a quiet "Adding"
  caption + plain titles list of the picked feeds above an "Add to" caption + destination
  cards (top level / folders), so only tappable things read as cards; **tapping a
  card commits all picked feeds there** (many feeds → one destination) and closes
  (`add/DestinationStep.vue`) → optional **new folder** — a bottom "New folder" card slides to a
  name input whose submit arrow creates the folder via `feedsStore.addFolder()` and pops back to
  the destination list (`add/FolderStep.vue`). Phases slide with the `panel-slide` classes in
  `transitions.css`. Headers follow the settings drawer's language: step 1 has an in-flow close
  above the title; steps 2–4 have a md caret back + `text-subtitle` title (no close). The search
  input is enlarged for mobile (taller padding, `text-body`, `rounded-2xl`).
  Committing calls `useFeedsStore().addFeed()` per picked feed, which `POST`s to `/feeds` and
  awaits the server's row (uids are minted server-side). Subscribing is the one step that can be
  **refused**, and the refusal surfaces in both places that commit: `add/DestinationStep.vue`
  and — for the folder-scoped add, which commits straight from the search step since it already
  knows its destination — `add/SearchStep.vue`. It's the API's `detail` verbatim ("That URL
  isn't a feed.", "You already follow that feed."), sitting **above** the destination list (the
  panel is `touch-none`, so anything below a long folder list is out of reach on mobile), with
  the destination cards disabled while the request is in flight; the sheet **only closes on
  success**. The search step calls
  **`GET /discover`** _(T11a, 2026-09-06)_: a pasted URL resolves whether or not it is the feed
  URL — a blog homepage or a post page, a YouTube channel URL or `@handle`, a subreddit URL or a
  bare name. Results a user already follows come back dimmed with a **"Following"** caption and
  can't be picked, and each row is captioned with its **feed URL**, since one page can declare
  several feeds and that is what tells them apart. A **keyword under the YouTube card** searches
  YouTube by channel name _(T11b, 2026-09-11)_: up to five channels, each row leading with the
  channel's avatar, and the same `videos.xml` feed URL a pasted channel resolves to, so subscribing
  is the same `POST /feeds` either way. YouTube refusing to answer (quota spent, key rejected) is
  a **503** the step shows as an error — not "nothing found", which would be a lie. A keyword
  under Website or Reddit still says "Nothing found. Try pasting a link." (T11c, T11d).
- **Edit drawer (folder / feed)** — `app/components/edit/Drawer.vue` hosts the sheet (UDrawer
  + open protocol + close-key provide + animation-end navigation), like the settings/add
  drawers; every `/edit/*` URL renders the home component (`pages:extend`) so the list stays
  behind the sheet on mobile. The route-driven panel switch and confirm-descriptor table live in
  `app/components/edit/Panels.vue` (`EditPanels`), shared by the mobile drawer and, on desktop,
  the content overlay. Opened by **long-press** on a folder or loose-feed home
  row (mobile, `useLongPress` — suppresses the follow-up nav click) or a **hover-revealed 3-dot**
  on the row (desktop only, `@media (hover: hover)`). Polymorphic by uid: a `folder_*` uid opens
  the **folder panel** (`edit/FolderPanel.vue` — rename input + a **Save** pill, a "Feeds"
  list of member feeds each row spanning the full drawer width with an on/off mute toggle
  (`ui/Toggle.vue`), a dashed full-width ghost row labelled "Add feed" that runs the add
  wizard scoped to this folder — skipping the destination step and returning here — and a
  `ui/DangerButton.vue` labelled "Delete folder"); a loose `feed_*` uid opens the **feed panel**
  directly (`edit/FeedPanel.vue` — edits the **name only**, with the RSS `feed_url` shown as
  read-only text below it (it lives on the shared global `Source`; [backend-roadmap.md](./backend-roadmap.md)
  § Contract resolutions, 3), back caret + `useSwipeBack`
  when reached as a folder member (`/edit/:uid/feed/:feedUid`), X close when standalone; its
  `DangerButton` reads "Remove from this folder" as a member or "Delete feed" standalone).
  Both the name and, in the folder panel, each member's mute toggle are staged as **local
  drafts** — toggling a mute enables the Save pill same as editing the name does, and nothing
  reaches the store until Save is pressed. Text/mute edits commit via an explicit **Save**
  `ui/PillButton.vue` (muted until a draft differs from the committed folder/feed), and
  pressing it also **closes the edit drawer**, returning to the home list.
  `ui/DangerButton.vue` is the app's one destructive affordance — an elevated full-width card, no
  icon, muted label — that **arms** on tap (`animate-pulse` + `text-error` for 250ms, deliberately
  under the 0.35s panel-slide since the red flip is instant) and then
  routes to a confirm sheet; it never mutates the store itself. Every destructive action now
  confirms before committing, via `edit/ConfirmPanel.vue` (replaces the earlier `DeleteConfirm.vue`;
  purely presentational — props `action`/`verb`/`subject`/optional `context`/`note`/`backTo`,
  emits `confirm`), rendered at three routes whose copy, back path, and store call are owned by a
  single `confirm` computed in `Panels.vue`: `/edit/:uid/delete` (delete the folder, or the
  standalone feed when `:uid` is a loose `feed_*`, branching on the prefix) and
  `/edit/:uid/feed/:feedUid/delete` (route name `edit-feed-delete`, registered in
  `nuxt.config.ts` `pages:extend`) which unlinks a member feed from the folder. Confirm/Cancel on
  the sheet itself are `ui/BlockButton.vue`. Row content in both panels is inset `sm` as real
  padding on the row (`pl-sm` on the link, `pr-sm` on the `li`) rather than a `text-inset` margin
  on the list, so row text lines up with the Name input, the RSS URL text, and the section
  headings.
  Panels slide with the shared `panel-slide` classes. Backing `feeds`-store actions:
  `renameFolder`, `setMutedFeeds` (replaces the folder's whole muted set in one immutable
  write — the folder panel's draft toggles it once, on Save), `updateFeed`, `removeFromFolder`,
  `deleteFeed`, `folderDeleteImpact`, `deleteFolder` — all of them API calls now (see **Data
  layer**). **The label divergence this file tracked is closed** _(2026-09-01)_: the shipped
  copy is now "Delete folder", "Delete feed" and "Remove from this folder" — the three actions
  [screens-and-flows.md](./screens-and-flows.md#7-create--edit-folders--feeds-from-the-home-list)
  § 7 already specced — and headings, aria-labels and route segments use
  [backend.md](./backend.md)'s nouns throughout, so a `Source` is never named on screen.
  A `/edit/*` route whose folder or feed can't be found — a stale link, or a store that never
  loaded — redirects to `/` instead of leaving an empty panel open, and the sheet doesn't open
  until the store has answered either way (`edit/Drawer.vue`, and the edit branch of the desktop
  `ContentOverlay.vue`), so a cold deep link no longer slides up an empty sheet and holds it for
  the length of `GET /home`.
- **Layouts** — `app/layouts/default.vue` is the single layout and the mobile/desktop branch
  point: `useIsDesktop()` (`app/composables/useIsDesktop.ts` — VueUse `useMediaQuery` at the
  `lg` 1024px tier, gated behind `useMounted` so SSR and the hydration render always emit the
  mobile tree, flipping only after mount on wide clients) chooses between the unchanged mobile
  tree (`lg:hidden`-masked for a wide first paint, hosting the three drawers) and
  `DesktopShell`. `isDesktopNow()` is the synchronous twin for imperative guards.
- **Desktop shell v1** (`app/components/desktop/`) — ≥1024px renders three columns composed
  straight from the route and the `feeds` store, not a nested-route tree: `Sidebar.vue` (18rem)
  — the shared `HomeFeedList` (wordmark, Home, Saved, folders, loose feeds — see Feeds list v1,
  below), then two standing rows, **Add feed** (→ `/add`) and **Settings** (→ `/settings`); a
  posts pane (24rem, `FeedPostList`); and a post pane (flexible, capped at a 42rem reading
  measure, `FeedPostView`, or a dimmed "Select a post" placeholder — **no auto-select**).
  `Shell.vue` reads `useRouter().currentRoute` rather than Nuxt's `useRoute()` (Nuxt's route
  object only resyncs when a `NuxtPage` resolves, and the shell renders none), syncing the
  feeds store's `readerFeedUid`/`readerPostUid`/`readerQuery`/`readerPath` on reader routes only
  — they stay frozen while a content route is open (which is what keeps a search alive across a
  trip into Settings).
  Settings, Add, and Edit present as a **content area** (`ContentOverlay.vue`) laid over the two
  reading panes; the sidebar stays interactive and the reading panes stay mounted underneath
  throughout (feed, selected post, search, and pane scroll all survive a round-trip). **Nothing
  on desktop slides** — the area appears and disappears like a page replacing a page, and the
  `.content-slide-*` classes are gone from `transitions.css` (see Resolved decisions → Desktop
  motion). Settings and Edit split the area into **two equal panes**, each `basis-2/5` — the
  posts pane's width, with the remaining fifth left empty on the right, because a form has a
  natural width and doesn't get better by getting wider the way an article does — a master pane
  (the settings section list, or a folder's panel) and a detail pane (the open section, or a
  folder member's panel / the scoped add steps / a delete confirm), each keeping the open item's
  row persistently **elevated with its label in `primary`** in the master (`activePath` on
  `SettingsHome`, `activeUid` on `EditFolderPanel` — the same treatment the feed list and post
  list use), with a "Select a section" / "Select a feed" placeholder in the detail pane until
  something is open. Two flows have no master to sit beside and take the area **single-pane**,
  capped at `--container-reading`: Add (the wizard is four linear steps with no list) and editing
  a **loose** feed (nothing below it to pick — a second pane there would be dead space beside a
  squeezed form). Switching what the detail pane shows is a plain swap with no motion, exactly
  like clicking a different post, and the add wizard's steps cut instead of sliding here
  (`AddSteps`'s `slide` prop, `false` from this host only). The area reuses the exact mobile
  panel components (`app/utils/settings-panels.ts`'s route map, `AddSteps`, `EditPanels` — which
  gained a `pane: 'all' | 'single' | 'master' | 'detail'` prop — `'all'` is the unchanged
  mobile-drawer behaviour, `'single'` the same views without the slide) and resets the add wizard
  on any exit from `/add` or `/edit/*`. The
  three drawer hosts guard their `onMounted` open-on-deep-load with `isDesktopNow()` so a
  desktop deep-load of `/settings/*`, `/add`, or `/edit/*` never flashes a bottom sheet.
  Layout tokens live in `app/assets/css/layout.css` (`--container-sidebar/postlist/reading/post`,
  a `@theme static` block in its own namespace so it doesn't collide with the six-name
  `--spacing-*` rule) — there is no whole-shell width cap. **v1 is deliberately unpolished:**
  keyboard focus rings still suppressed, and `HomeOptionsDrawer` still opens as a bottom sheet
  on desktop — both queued for a later design/polish pass.
- **Empty / unreachable state** — `app/components/home/EmptyState.vue` carries two states in one
  layout: the first-run nudge ("Nothing here yet" + an explainer + a primary "Add your first
  feed" action → `/add`), driven by the `feeds` store's `hasFeeds` computed (feeds or folders
  non-empty), and — when `GET /home` failed — "Can't reach the server" + a **Try again** action
  that retries the load. Neither renders until the store is `loaded` (or has failed), so the
  first paint can't flash "Nothing here yet" while the request is in flight. Shown on the mobile
  home page in place of the list, and on desktop in place of both reading panes (the sidebar
  keeps working, so Add feed stays reachable). New spec surface — nothing was specced for the
  zero-feeds state before.
- **API client & types** — `runtimeConfig.public.apiBase` (default
  `http://localhost:8000/api/v1`, override `NUXT_PUBLIC_API_BASE`) and `app/plugins/api.ts`,
  a `$fetch.create` instance (`$api`) that is the one way the app talks to the server: it
  attaches `Authorization: Bearer` on request and, on a 401, clears the session and redirects to
  `/login` (inside `nuxtApp.runWithContext`, since an ofetch hook runs outside the Nuxt
  context). Types are **generated from the API**: `pnpm types:api` runs `openapi-typescript`
  against `/api/v1/openapi.json` into `app/types/api.d.ts` (committed, so typecheck doesn't need
  Docker; ESLint-ignored). `app/assets/types.ts` survives as a thin alias layer over
  `components['schemas']` — `Feed`, `Folder`, `Post`, `FeedType`, plus `Home`/`PostPage`/
  `Settings`/`Me`/`SavedGroupName` — so component imports are unchanged and a renamed backend
  field breaks typecheck instead of silently rendering blank. `FeedCandidate` is generated too as of
  T11a — `DiscoverResultSchema`, which is a `Feed` minus its uid plus `already_subscribed`.
- **Auth & login** — `app/pages/login.vue` (brand, one line, then **two controls**: Google's
  rendered sign-in button and, below it, the dev-token field — both ship, see Not started →
  Sign-in (rest); `definePageMeta({ layout: false })` is load-bearing, since the default
  layout renders `DesktopShell` instead of the page above 1024px). The Google button is loaded
  with VueUse `useScriptTag` and rendered by Google Identity Services into a wrapper that
  **clips its iframe's 10px bleed**; its chrome is Google's (hence `theme: 'outline'` — a clipped
  dark button inverts the app's elevation direction), and the column is capped by a new
  `--container-signin` (29rem) because Google caps its button at 400px. A missing
  `runtimeConfig.public.googleClientId` renders no button at all and leaves the dev field as the
  way in. `app/stores/auth.ts` holds the token (cookie-persisted, `pick: ['token']` only) and the
  `/me` profile; `signInWithToken()` proves a token against `/me` before keeping it, so a bad
  token fails on the login screen instead of as a redirect loop, and `signInWithGoogle()` only
  adds the step before it — `POST /auth/google`, then hand the returned token to the same path.
  Errors are **one message per control**, and `app/plugins/api.ts`'s global 401 handler skips
  `/auth/google`, so a refused credential leaves a live session untouched.
  `app/middleware/auth.global.ts` is a **pure guard** — everything except
  `/login` needs a token, and it does no fetching (see Resolved decisions → Backend stack & API
  → T6). Sign out (Settings → Account) revokes the token server-side via `POST /auth/logout`,
  clears both stores, and returns to `/login`; Account's "Signed in with" row reads `google` for
  a linked account even in a dev-token session, because `provider` describes the account.
- **Data layer** — the `feeds` store loads `GET /home` once (in-flight-guarded; a failure is
  swallowed rather than raised, so it can never surface as Nuxt's error page, and retries from
  the home screen's **Try again** or the next app boot) into feeds, folders and `savedCounts`,
  behind a `loaded` gate and an `unreachable` flag; the response's `order` is applied as a sort at load time and not retained
  (the list renders as folders-then-loose-feeds; interleaving waits on the reorder UI — see
  Not started → Home reorder).
  `app/composables/usePostList.ts` cursor-pages `GET /feeds/{uid}/posts` (limit 10) behind a
  sentinel + VueUse `useIntersectionObserver` rooted on the viewport, so the same composable
  serves the mobile page scroll and the desktop pane; given a query it pages `GET /search`
  instead, with the uid as `scope` — same page shape, same cursor, same failure rules, so
  searching is a different URL and nothing else, and a changed query resets the list exactly as
  a changed uid does. `app/composables/usePost.ts` owns one post
  plus its save toggle. The `settings` store loads `GET /settings` and `PUT`s on change (a full
  replace of all three synced fields). Both loads run from
  `app.vue`'s `onMounted` (and again on sign-in), never from middleware — see Resolved decisions.
  **Writes** _(2026-09-01)_: every `feeds`-store action calls the API. `renameFolder`,
  `setMutedFeeds`, `updateFeed`, `removeFromFolder`, `deleteFeed` and `deleteFolder` are
  **optimistic with rollback** — the local array is replaced first and a shared `commit()` helper
  restores the previous one if the request fails (the cascading `deleteFolder` re-reads `/home`
  instead, via the store's new `reload()`, since its effect spans both arrays). `addFeed` and
  `addFolder` **await** instead and let their error escape to the add wizard, because the backend
  mints every uid. Membership is sent whole: `removeFromFolder` `PATCH`es the surviving
  `feed_uids`.
- **Feeds list v1** — `app/components/home/FeedList.vue` (`HomeFeedList`) renders the home list
  from the `feeds` store's `/home` load — used by the mobile home page (`app/pages/index.vue`)
  and, on desktop, the sidebar (an `activeUid` prop drives the desktop persistent-selection
  highlight). It leads with a stand-in **FEEDME wordmark** (`text-logo`, FEED in `text-primary`,
  ME in body ink — a placeholder until a designer supplies a real mark; see
  [design-system.md](./design-system.md) § Type scale; the mark itself links to `/feed/all`, the
  link sized to the text so the row's dead space isn't a target), then **Home** as an ordinary list row —
  same height and surface as every other row, inline `Home` + an `All feeds` caption — linking
  to `/feed/all` (the merged all-feeds read), then a pinned **Saved** row (links to
  `/feed/saved`; chevron expands to the three saved groups — Bookmarks / Favorites / Later from
  `app/utils/saved.ts`, each → `/feed/saved_*`, each showing its count from `/home`'s
  `saved_counts`, the same muted count a folder row carries), then folder rows (name + feed
  count, expand/collapse chevron with auto-animate and an accent tap flash, sitting **inside**
  the row's tap-flash card surface at IconButton size on the navbar buttons' vertical axis;
  members indented and greyed when muted), then loose feeds; every row links to `/feed/[uid]`.
  Chevrons point **right** when collapsed and rotate to down when expanded. Home's trailing
  3-dot — sitting where folder rows keep their chevron, directly below the navbar **+** — opens
  a **half-height options sheet** (`app/components/home/OptionsDrawer.vue`, local-state drawer —
  not route-driven — with placeholder rows: New folder / Edit feeds / Reorder feeds). Names only
  for now — no type icons. A row's trailing action is hover-revealed on hover-capable pointers
  (`@media (hover: hover)`); on touch it hides for a folder/loose-feed row, where long-press is
  the entry (below), but stays visible for Home's 3-dot, which has no long-press fallback. Every
  row also carries the shared desktop `hover-accent` (label to `primary` on hover), and a
  selected row — the tap flash on mobile, the persistent desktop selection — lights its **name**
  `primary` on top of the elevated surface, since in cards mode every top-level row already has
  a surface and the name is the only cue left; a muted member is dimmed by opacity alone so it
  still takes both. In list mode rows sit `2xs` apart so a selected row's rounded surface doesn't
  fuse with its neighbour. See [design-system.md](./design-system.md) § Color roles → Hover
  state. Long-press (mobile) /
  hover 3-dot (desktop) on a folder or loose-feed row opens the **edit drawer** (see Built,
  below).
- **Feed page v1** — `app/components/feed/PostList.vue` (`FeedPostList`, `uid` + `q` +
  `activePostUid` props) lists PostCards with the resolved feed/folder name as title — used by
  the mobile feed page (`app/pages/feed/[uid]/index.vue`) and, on desktop, the shell's posts
  pane. Posts come from `usePostList(uid, q)` — the uid resolves **server-side** in the
  frontend's own order (`all` → `saved` → `saved_*` → `folder_*` → `feed_*`), so the component
  filters nothing and just renders what pages in; a uid change resets the list rather than
  appending. The list says "No posts here yet" when a stream is genuinely empty and "Couldn't
  load posts." when a page request failed (paging stops rather than retrying into a refusing
  server).
  **Search** lives on the title row: a magnifying-glass `IconButton` swaps the title for a
  `SearchInput` (placeholder "Search *{title}*", so the list being searched is named without a
  noun that would be wrong for a folder or Saved; no submit arrow — the field is live) and back
  to an X that closes it. Typing is debounced 300ms into `?q=` on the route via `router.replace`
  (never `push` — Back must leave the page, not walk the term backwards), and the list pages
  `GET /search` scoped to the same uid, ordered by recency; an empty result says *No posts match
  "…"* with the term. The host owns the query the way it owns the uid: the mobile page reads `route.query.q`
  (frozen the moment the page starts leaving, so results don't blank mid-slide), the desktop
  shell the store's `readerQuery` mirror. A result's link carries the query, so Back from a post
  lands on the results, and a deep link with `?q=` opens the box filled. Closing is immediate; a
  uid change clears it. The mobile navbar's magnifying glass is gone — this row is the entry on
  both viewports, since the desktop pane has no navbar.
  `feed/[uid].vue` stays a `<NuxtPage/>` passthrough on
  mobile; on desktop the shell bypasses it (and every route's `<NuxtPage/>`) entirely, composing
  the posts/post panes itself from the feeds store.
- **Post page v1** — `app/components/feed/PostView.vue` (`FeedPostView`) renders title, date and
  the post's `summary`; it is **presentational** — the host that owns the uid (the mobile post
  page, or the desktop shell for its post pane) fetches through `usePost(uid)` and passes the
  post down, because the host also needs the title and the save state. The mobile navbar's
  bookmark is wired: it toggles `PUT`/`DELETE /posts/{uid}/save` into **Bookmarks** (Save is a
  toggle, not a group chooser) and reflects the saved state in its icon and `aria-pressed`. The
  **desktop post pane has no action bar**, so saving is mobile-only for now (it never had one —
  queued with Desktop polish). Summaries are RSS HTML and are rendered as **plain text**
  (`app/utils/strip-html.ts`) — nothing sanitises third-party markup, and the extracted article
  text is the real answer; T10 built `/posts/{uid}/article` _(2026-09-05)_ but this component
  does not call it yet (see Not started → Post page (rest)). Open source is still missing on both
  viewports.
- **PostCard v1** — `app/components/feed/PostCard.vue`: date + title only (no image / type cue
  yet), whole card links to the post; rows separated by spacing (no divider lines).
- **Context-aware navbar** — both slots swap per page: home = menu + add, feed page =
  sidebar icon (→ home) alone (search sits on the list's title row instead — see Feed page v1),
  post page = back (→ its feed, carrying the search it was opened from) + save (wired — see Post
  page v1). Navigation is hierarchical, not history-based.
- **Reader slide transitions** — **mobile only** (the desktop shell renders no `<NuxtPage/>`,
  so this machinery never runs there — see Desktop shell v1). home → feed → post slide like a
  navigation stack (deeper pushes in from the right, back pops out to the right). Direction is
  set on route meta by `app/middleware/page-slide.global.ts` (computed *before* render — a
  component watch is one navigation late), shared `.page-slide-*` classes live in
  `assets/css/transitions.css`, and the default layout provides the positioning/clip context.
  Non-reader routes (add, settings) swap instantly (`page-none`) so their drawer animations own
  the motion; the settings drawer's internal slides — and the edit sheet's, and this
  middleware's own direction check — share one push/pop rule and its CSS variables in
  `app/utils/panel-slide.ts` (`panelSlideDirection`/`panelSlideVars`, replacing three copies of
  the same logic). An **equal-depth** move (one settings panel to a sibling, one folder's edit
  to another's) now slides **not at all**, rather than incorrectly animating as a push — the bug
  the consolidation fixed.
- **Swipe navigation** — `app/composables/useSwipeNav.ts` (VueUse `useSwipe`, touch-only).
  `useSwipeBack`: swipe right anywhere on the feed page, post page, a settings subpage, or an
  edit-feed subpage drags the page with the finger and past 72px pops to the parent route
  (reusing the page-slide / panel-slide pop); under threshold it snaps back. `useSwipeOpen`: swipe left
  on a home feed row or settings section row nudges it and opens it (gesture twin of
  tapping; one delegated listener per list). Axis-locked so vertical scrolling and vaul's
  drag-to-close are untouched; back buttons unchanged.

## Stubs (exist but placeholder content)

- **Add-feed search by keyword, outside YouTube** — pasting a URL of any kind resolves for real
  (T11a), and a channel name under the YouTube card searches YouTube (T11b) — see Built, and
  [backend-roadmap.md](./backend-roadmap.md). What's still a stub is a **keyword under Website
  or Reddit**: subreddits by name is T11c, our own catalog T11d. Until then those two cards report
  "Nothing found. Try pasting a link."

## Not started

- **Post page (rest)** — Open source, and the **article text** itself. The endpoint behind it now
  exists — `GET /posts/{uid}/article`, built and cached in T10 _(2026-09-05)_ — but **nothing on
  the frontend calls it**: `FeedPostView` still renders the stripped RSS `summary`, so no screen
  has yet shown an extracted article or exercised its `unavailable` fallback. Wiring the reader
  (render `article_html` as markup, keep the stripped summary as the fallback, add Open source) is
  the follow-up recorded in [backend-roadmap.md](./backend-roadmap.md) § Tasks → T10.
- **Desktop polish** — v1 (see Built → Desktop shell v1) ships the structural three columns
  only: keyboard focus rings still globally suppressed,
  and `HomeOptionsDrawer` still opens as a mobile-style bottom sheet on desktop. The post pane
  has **no action bar**, so the save toggle is mobile-only. Auto-selecting
  a detail post (e.g. the last-read one) on entering a feed is also deferred — v1 always starts
  at the "Select a post" placeholder.
- **Settings content** — the drawer, its four subpages, and transitions are built, and
  Appearance and Account are real (see Built); About's version string is hardcoded and Report
  still needs real content and a way to actually send anything.
- **PostCard (rest)** — image and source-feed type cue.
- **Add feed (rest)** — keyword search for subreddits and our own catalog (T11c, T11d), a
  candidate's latest posts before subscribing (T14, planned — `GET /discover/posts`), sub counts,
  and input validation via VeeValidate/Zod. The wizard UI, RSS discovery from a pasted URL,
  YouTube search by name and the subscribe itself are built (see Built) — any URL works end to
  end.
- **Saved posts (rest)** — saving, unsaving and reading the saved streams work end to end (see
  Built), but every save lands in **Bookmarks**: there is no group chooser and no way to move a
  post between Bookmarks / Favorites / Later, though the API call for it is the same upsert.
- **Folders (rest)** — the expandable rows on the home list, the merged-stream read, **folder
  creation inside the add wizard** (`addFolder` store action + `add/FolderStep.vue`), the **edit
  drawer** and every folder write (`POST`/`PATCH`/`DELETE /folders`) are done. Still missing: the
  actions behind the home options sheet (New folder / Edit feeds / Reorder feeds are still
  placeholder rows) and a standalone folder-creation entry point with member picking. See
  [data-model.md](./data-model.md#folder) and
  [screens-and-flows.md](./screens-and-flows.md).
- **Sign-in (rest)** — Google sign-in works end to end (see Built → Auth & login), but the
  **dev-token field is still on `/login` for everyone**, deliberately: the natural retirement is
  gating it on `import.meta.dev`, and gating it at build time today would make it vanish silently
  the day a production deploy exists. No native Google sign-in either — the Capacitor plugin is
  the other half of [backend.md](./backend.md#auth) § Auth's step 1, and no Capacitor build
  exists yet. Noted for a deploy: `ux_mode: 'popup'` needs a
  `Cross-Origin-Opener-Policy: same-origin-allow-popups` header if one is ever set.
- **Home reorder** — `PUT /home/order` exists and is strict, but **nothing drives it**: the home
  list has no drag-and-drop, and the options sheet's Reorder feeds row is a placeholder. The
  `order` from `/home` is applied as a sort at load and not retained, so the UI, when it lands,
  re-reads `/home` after writing.

## Installed but unused

- **VeeValidate + Zod** — not wired into any form yet.
- **@vueuse/motion** — available for animations.

## Open decisions

_None currently._

## Resolved decisions

- **Post search presentation** _(recorded 2026-09-15)_ — the question T12 left open (mobile
  sheet vs. centered dialog) is settled as **neither**: the search box swaps in for the list's
  title on the same row, in `FeedPostList.vue`, so the mobile feed page and the desktop posts
  pane share one entry point. The query lives on the route as `?q=` (debounced, `replace` not
  `push`), which is what makes a deep link, a reload, and Back from a post all land on the same
  results. See Built → Feed page v1.
- **Desktop motion** _(recorded 2026-09-15)_ — **nothing slides on desktop.** The content area
  (Settings / Add / Edit) replaces the reading panes the way a new page would, the add wizard's
  steps cut, and detail-pane swaps were already plain. Sliding is the mobile stack's language:
  there one pane is the whole screen and the motion says which way you moved; on desktop both
  ends of a move are on screen at once, so it would only be decoration. This closes the "no
  desktop pane/overlay transitions" item that Desktop polish carried as a gap.
- **Desktop layout composition** _(2026-07-27)_ — desktop (≥1024px) is **three columns**
  (sidebar + posts pane + post pane), composed by `app/layouts/default.vue` /
  `DesktopShell` straight from the existing routes and the `feeds`/`settings` stores —
  **not** a nested-`<NuxtPage/>` master/detail tree (tried twice; a child navigation
  under a nested page remounts the parent, nuxt#13094 — see
  `.claude/memory/project-gotchas.md`). On desktop, no route renders a `<NuxtPage/>` at
  all; the routes and `pages:extend` records are unchanged, so the mobile tree still
  works exactly as before. This settles the "Routing scheme" decision below toward
  layout-composed panes rather than nested routes for the desktop half of that promise.
- **Desktop breakpoint** _(2026-07-27)_ — a single 1024px tier (Tailwind `lg`) for v1:
  below it the app is the mobile structure, at or above it the desktop shell. A
  middle tablet tier is possible later but not built.
- **Desktop detail-pane selection** _(2026-07-27)_ — the post pane shows a placeholder
  ("Select a post") until a post is clicked; there is no auto-select of the first or
  last-read post. Revisit later if that feels wrong in daily use.
- **AI reading-companion feed** _(2026-07-16)_ — a custom RSS feed of AI-written posts
  (one per book chapter, reflection + link back to the chapter) is specced in
  [ai-feed.md](./ai-feed.md). Lives in a separate `feedme-books` repo (Python; batch
  generation → manual review → all-at-once or daily-drip release rebuilding `feed.xml`);
  zero FeedMe changes — it's just another Source once the backend lands. Nothing is
  implemented yet.

- **Backend stack & API** _(2026-07-12)_ — the fetching + persistence stack is specced in
  [backend.md](./backend.md): Django + django-ninja + Dramatiq + Postgres + Redis in
  `backend/` (monorepo, Docker Compose). Global shared sources polled once, per-user
  Feed/Folder/SavedPost/Settings layer, Google OAuth with opaque bearer tokens, Postgres
  FTS + trigram search behind an engine-neutral `/search`, on-demand article extraction,
  ~90-day retention for unsaved posts. Endpoint catalog and decision log live there.
  **Hello world is running** _(2026-08-07)_: `backend/` is a Django 5.2 + django-ninja
  project (package `feedme`) with one endpoint, `/api/v1/health`, ninja's auto-generated
  docs at `/api/v1/docs`, an OpenAPI schema at `/api/v1/openapi.json`, and Django admin at
  `/admin/`. `docker-compose.yml` at the repo root runs `api` (port
  8000, code bind-mounted), `db` (Postgres 16, healthchecked, `pgdata` volume), and `redis`;
  `worker`/`scheduler` joined the stack in T9 _(2026-09-03)_ — see below. `.env.example` is at
  the repo root.
  **Models are in** _(2026-08-07)_: the Django app `backend/core/` implements
  [backend.md](./backend.md)'s § Data model exactly — all 9 tables (custom `core.User` as
  `AUTH_USER_MODEL` with a unique nullable `google_sub` and email login, `AuthToken`,
  `Source`, `Post`, `Feed`, `Folder`, `FolderMember`, `SavedPost`, `UserSettings`), the
  spec's unique constraints and cascade/`PROTECT` rules, and uid minting via
  `core/uids.py`'s `make_uid(prefix)` (the backend mints `source_*`/`post_*`/`feed_*`/
  `folder_*`, per the vocabulary table). All models are covered by Django admin (Source
  gets the ops treatment — active/error-count visibility; **reshaped 2026-09-01** so that
  settings, feeds, folders, saved posts and sessions are edited as inlines on the user's own
  page and only the global tables are listed on the index). One migration
  (`core/migrations/0001_initial.py`), an idempotent `ensure_superuser` management command
  driven by `DJANGO_SUPERUSER_*` env vars, and a dev `entrypoint.sh` (migrate →
  ensure_superuser → runserver) wired into the Dockerfile. Verified: full stack bootstrap
  from an empty volume, an ORM smoke test of every model + its cascades, `/api/v1/health`
  200, admin login page serving. Still not built: API endpoints beyond `/health`, the auth
  guard, Google OAuth, the fetching pipeline/Dramatiq, and search (tsvector/GIN/trigram,
  deferred to a dedicated search session) — everything else `backend.md` specs is still the
  agreed target, not built. **Sequenced _(2026-08-19)_:** the remaining work is split into 13
  dependency-ordered tasks in [backend-roadmap.md](./backend-roadmap.md), starting with CORS +
  the test harness, then bearer-token auth, and reaching a deliberate checkpoint at T6 where
  the Nuxt app is wired to real data before the backlog grows further.
  **T1 landed _(2026-08-19)_:** CORS via `django-cors-headers` (allowed origins from
  `CORS_ALLOWED_ORIGINS`, defaulting to `http://localhost:3000`, middleware first in the chain),
  `ruff` + `pytest`/`pytest-django` configured in `backend/pyproject.toml`, a `user` fixture in
  `backend/conftest.py`, and `backend/tests/` covering `/health`, CORS preflight (allowed and
  foreign origin) and the custom user model. `SECRET_KEY` now raises `ImproperlyConfigured`
  instead of silently using the dev key when `DEBUG` is off. Verified: `pytest` green in the
  container, `ruff check` clean, and a real `fetch()` from a page on `localhost:3000` reaching
  `/api/v1/health` with no CORS error.
  **T2 landed _(2026-08-23)_:** the API is now login-only. `backend/core/auth.py` mints
  opaque tokens (`secrets.token_urlsafe(32)`, stored SHA-256-hashed, sliding 30-day window
  measured from `last_used_at` and touched at most hourly) and its `BearerAuth` guard is wired
  globally via `NinjaAPI(auth=…)`. `/health` is the one `auth=None` opt-out, and now backs a
  compose healthcheck on the `api` service. Endpoints moved into `backend/core/api/`:
  `account.py` serves `GET /me` (email, member-since, provider — the three lines
  `settings/Account.vue` hardcoded at the time), `DELETE /me` and `POST /auth/logout`, and
  `errors.py` holds the single `{"detail": string}` error body. `manage.py issue_token
  <email>` prints a usable token, so every later endpoint is testable before Google OAuth
  lands in T8. Verified: 21 tests green, `ruff` clean, and a real curl loop — 401 without a
  token, 200 with one, 204 on logout, 401 again straight after.
  **T3 landed _(2026-08-25)_:** the database holds real posts. `backend/core/ingest.py`
  exposes one synchronous `ingest_source(source)` — conditional GET with `requests` (explicit
  connect/read timeout, `If-None-Match` / `If-Modified-Since` from the stored validators),
  early return on 304, `feedparser` on the bytes, then upsert by `(source, guid)` so a re-poll
  updates a post in place and keeps its `post_*` uid. Entry mapping covers all three source
  types: `media:thumbnail` for YouTube posters, image enclosures for blogs, `published` over
  `updated` for the timeline. Failures never raise — `error_count` climbs, `next_fetch_at`
  backs off exponentially to a 24h cap, and the source deactivates after five in a row, with a
  **Reset errors and poll on the next run** admin action as the way back. Driven by
  `manage.py poll_source <source_uid>` and `manage.py poll_due`; T9 wraps the same function in
  a Dramatiq actor. Verified: 50 tests green, `ruff` clean, and the three mock sources polled
  for real — 10 Medium + 15 YouTube + 25 Reddit posts, a second `poll_due` correctly reporting
  nothing due, and a manual re-poll returning 0 new / 25 updated. Next is T4 — `/home` and
  `/settings`.
  **T4 landed _(2026-08-25)_:** the app's cold-start round-trip and account-level preferences
  are real. `backend/core/api/home.py`'s `GET /home` returns one aggregate — folders, every
  feed (with `Source`'s `type`/`site_url`/`feed_url`/`icon_url` flattened onto it, `type` typed
  as a `Literal` matching `app/assets/types.ts`'s hand-written `FeedType` union, so `source_uid`
  never leaks), the shared top-level order, and saved counts — in a constant 5
  queries no matter how many feeds an account has; `PUT /home/order` writes the one shared
  0..n-1 sequence across `Folder.order` and `Feed.order` in a transaction, and strictly rejects
  (422, naming the offending uids) a duplicate, a foreign uid, a folder-member uid, or a
  top-level uid left out, writing nothing on failure. `UserSettings` gained `scrollbar_style`
  (migration `0003_usersettings_scrollbar_style.py`, mirroring `app/stores/settings.ts`'s
  `thin`/`comfortable`/`auto`); `backend/core/api/settings.py`'s `GET`/`PUT /settings` read and
  fully replace it, `theme`/`feed_list_style`/`scrollbar_style` typed as `Literal` unions, with
  `GET` answering from an unsaved instance rather than creating a row on read. Verified: 76
  tests green (was 51), `ruff` clean, and against the real dev database — `/home` returning the
  three real feeds and a folder (one member muted) with correct top-level ordering, a reorder
  round-tripping through `PUT /home/order`, all three 422 branches firing correctly, and
  `/settings` returning defaults with no row then round-tripping through a `PUT`. Next is T5 —
  posts: list, detail, save.
  **T5 landed _(2026-08-26)_:** the posts are readable. `backend/core/postlist.py` owns the
  polymorphic uid in the frontend's own order — `all` → `saved` → `saved_*` → `folder_*`
  (members minus the ones muted in *that* folder) → `feed_*` — plus the base64 keyset cursor
  and the rule for which posts a caller may open at all: one from a source they subscribe to,
  or one they have already saved, so a saved post stays readable forever after unsubscribing.
  `backend/core/api/posts.py` serves `GET /feeds/{uid}/posts` (`?cursor=&limit=`, default 10,
  capped at 100, newest-first) in a constant **2 queries whatever the page size** — the caller's
  sources and the three fields that depend on who is asking (`feed_uid`, `saved_group`,
  `saved_at`) are correlated subqueries rather than joins. `feed_uid` resolves the global source
  to *your* feed and is `null` when you no longer have one; `saved_group` is `null` until you
  save, so a card renders its save state without a second request. Saved lists order by
  `saved_at`, everything else by `published_at`. `GET /posts/{uid}`, `PUT /posts/{uid}/save`
  (an upsert — moving between groups is the same call, and `saved_at` survives the move) and
  `DELETE /posts/{uid}/save` (idempotent, so a double-tapped toggle is a no-op) round it out.
  Verified: 108 tests green (was 76), `ruff` clean, and against the real dev database — paging
  the 50 real posts eight pages at a time with no repeat and no skip, every uid branch returning
  the right set, a save round-trip that `/home`'s `saved_counts` agrees with, and
  `/api/v1/openapi.json` carrying `feed_uid: string | null` and the `saved_group` union that T6
  generates TypeScript from.
  **T6 landed _(2026-09-01)_:** the frontend runs on this API — the checkpoint the roadmap was
  built around. Sign-in is a dev token on a new `/login` screen, proven against `/me` before
  it's kept; `app/plugins/api.ts` is the single `$api` instance that attaches the bearer and
  turns a 401 into a redirect; the `feeds` store loads `GET /home`; `usePostList(uid)`
  cursor-pages `GET /feeds/{uid}/posts` behind an intersection sentinel; `usePost(uid)` reads a
  post and toggles `PUT`/`DELETE /posts/{uid}/save`; the `settings` store round-trips
  `GET`/`PUT /settings`; and Settings → Account shows the real `/me` profile with a working
  Sign out. Types are generated from the OpenAPI document into `app/types/api.d.ts`
  (`pnpm types:api`), with `app/assets/types.ts` reduced to aliases over it, so the two sides
  can no longer drift. `app/assets/data.ts` and `app/assets/mock-search.ts` are **deleted** — no
  fallback path. Four decisions worth knowing, all in
  [backend-roadmap.md](./backend-roadmap.md) § Decision log (2026-09-01, T6): SSR renders the
  shell but **every API call is client-only** (the token never reaches the Nuxt server, which is
  how Capacitor will behave); the account's data loads in `app.vue`'s `onMounted`, **not** in
  middleware, because filling the stores before the hydration render is a real mismatch against
  a server render done on empty stores; each store captures `useNuxtApp()` at setup, since an
  action can run past an await where no Nuxt context exists; and the open post is fetched by its
  host rather than through a shared `useAsyncData` entry, which the mobile/desktop swap at the
  `lg` breakpoint clears out from under the survivor. An unreachable API is its own state
  ("Can't reach the server" + Try again), never the first-run empty state. Verified: `pnpm lint`
  and `pnpm typecheck` clean, and against the running API — sign-in on both viewports, all five
  post-list uid branches, paging 50 posts with no repeats, a save surviving a reload, the
  settings round-trip, sign-out revoking server-side, and the 401 redirect. Next is T7 —
  subscribe and folder writes.
  **T7 landed _(2026-09-01)_:** the app writes. `backend/core/api/feeds.py` adds `POST /feeds`
  (`{feed_url, folder_uid?}`) — find-or-create the global `Source`, with its `type` inferred
  from the host rather than taken from the request, and for a **brand-new** source run T3's
  `ingest_source()` **inline**, because fetching the feed is the only honest way to know a URL
  is one; on failure the source row is deleted again and the caller gets a 422 ("That URL isn't
  a feed."), so a typo leaves no dead global row. A source that was deactivated when its last
  subscriber left is reactivated instead. `PATCH /feeds/{uid}` renames (name only, contract
  resolution 3) and `DELETE /feeds/{uid}` unsubscribes — memberships cascade at the database
  level, and the source is then deactivated rather than deleted, because its posts and other
  readers' saves outlive your subscription. `backend/core/api/folders.py` — tagged **`home`**,
  since a folder is home-screen structure — adds `POST /folders`, `PATCH /folders/{uid}` (name,
  members and mutes each optional, so the folder panel's single Save is a single call) and
  `DELETE /folders/{uid}`, returning the same `unsubscribed_count` the confirm sheet predicted.
  Both obligations T4 left behind are settled there: a membership write verifies every feed uid
  belongs to the caller, and a feed freed from its last folder is rehomed to the end of the
  top-level order. `PUT /home/order` now reads, validates and writes inside one transaction
  under `select_for_update()`, closing T4's recorded review note. On the frontend every
  `feeds`-store write calls the API — optimistic with rollback, except the two creates, which
  await the server-minted uid — the add wizard subscribes a pasted feed URL for real and shows
  the API's refusal on the destination step instead of closing, and the edit drawer's copy,
  aria-labels and route segments (`/edit/:uid/feed/:feedUid`) moved onto
  [backend.md](./backend.md)'s vocabulary. Eight decisions are recorded in
  [backend-roadmap.md](./backend-roadmap.md) § Decision log (2026-09-01, T7). Verified: 159
  backend tests green (was 108), with a test per cascade rule, `ruff` clean, `pnpm lint` and
  `pnpm typecheck` clean, and the flow driven in a real browser at both viewports — subscribe by
  URL with the real title backfilled, the not-a-feed 422 leaving no source behind, rename,
  rename + mute in one save, all three cascade rules with their counts, re-subscribing
  reactivating a deactivated source, and an offline write rolling back.
  **T8 landed _(2026-09-03)_:** sign-in is real. `POST /auth/google` verifies the id_token Google's
  button returns (`backend/core/google_auth.py`, `google-auth` — signature, issuer, audience,
  expiry, and a verified email) and answers with **our bearer token alone**; the profile still
  comes from `/me`. An account is found by `google_sub`, else linked onto a row with the same
  verified email **that no Google account has claimed** (a claimed one is a 401 — an email can be
  reassigned, a `sub` can't), else created. On the frontend `/login` renders Google's button above
  the dev-token field and `signInWithGoogle()` hands its token to `signInWithToken()`, so there is
  one path after "set the token". **The dev path stays** — a deliberate reversal of T8's own plan
  and of the T6-era decision that promised its deletion; see
  [backend-roadmap.md](./backend-roadmap.md) § Decision log (2026-09-03, T8) for that and ten
  more, including why `provider` describes the account rather than the session, why a changed
  Google email never rewrites the stored one, and the two layout decisions Google's button chrome
  forced.
  Verified: 172 backend tests green (was 159, 13 of them new for sign-in), `ruff` clean, and the
  screen driven in a real browser — a rejected credential reported on the button's own line while
  a live session and its route stay untouched, and the button's chrome measured there rather than
  guessed. Next is T9 — Dramatiq, `worker`, `scheduler`.
  **T9 landed _(2026-09-03)_:** polling runs on its own. `backend/feedme/broker.py` is the one
  module that knows Dramatiq exists — it calls `django.setup()` (load-bearing for the
  `dramatiq`/`periodiq` CLIs, a no-op under `manage.py`), builds a
  `RedisBroker(url=settings.REDIS_URL)`, and adds periodiq's `PeriodiqMiddleware` plus a
  hand-written `DjangoConnections` middleware that closes stale per-thread database connections
  around every message, since nothing in a worker fires Django's request-started/finished
  signals. `backend/core/tasks.py`'s `poll_source(source_uid)` wraps T3's `ingest_source`
  unchanged (`max_retries=3`, a 2-minute time limit) and returns quietly — no exception — on a
  uid whose source has since been deleted or deactivated, because Dramatiq's retries cover only
  what can throw; a dead feed already has its own `error_count`/backoff, and the two error
  models deliberately don't overlap. `poll_due_sources()` is periodiq's cron sweep (every 5
  minutes, targeting the ~30-minute per-source cadence) — it **claims** its batch with a plain
  `update()` before sending, since `ingest_source` only pushes `next_fetch_at` out when a poll
  *finishes*; without the claim, a sweep would re-enqueue everything still queued or in flight.
  `backend/core/ingest.py`'s write phase (`_upsert_posts` → `_backfill_source_metadata` →
  `_record_success`) now runs inside one `transaction.atomic()`, so a worker killed mid-poll
  leaves nothing half-written. `docker-compose.yml` gained `worker`
  (`dramatiq core.tasks --processes 2 --threads 4`) and `scheduler` (`periodiq -v core.tasks`),
  sharing `api`'s image through a new `x-backend` YAML anchor so the three can't drift apart;
  both skip the migrate/bootstrap entrypoint and wait on `api`'s healthcheck instead, since only
  `api` should touch the schema. `manage.py poll_source`/`poll_due` survive as the manual
  override, and `POST /feeds`'s inline fetch (T7) was deliberately left alone — validating a
  brand-new subscribe is still a synchronous request. Eight decisions are recorded in
  [backend-roadmap.md](./backend-roadmap.md) § Decision log (2026-09-03, T9), including the two
  error models, the claim-before-send reasoning, and why plain `dramatiq[redis]` was chosen over
  `django-dramatiq`.
  Verified: 182 backend tests green (was 172), `ruff check` clean, and against the running
  stack — the scheduler fired unattended, enqueueing 4 due sources the worker polled across its
  threads in under 2 seconds (70 → 129 posts, all four rescheduled with jitter); a `SIGKILL` sent
  mid-poll against a deliberately slow feed left the source with zero posts and `error_count`
  untouched, and the redelivered message polled cleanly after the broker's heartbeat window; a
  `SIGTERM` let the in-flight poll finish before shutting down; and `POST /feeds` still validates
  inline exactly as T7 left it.
  **T10 landed _(2026-09-05)_, on the server only:** `GET /posts/{uid}/article` extracts a post's
  article on the first request for it and serves everyone from `Post.article_html` after — the
  cache is global because the post row is. It reuses T5's visibility rule, so a post you neither
  follow nor saved 404s as detail does. Extraction runs **synchronously with a hard timeout**
  inside the request rather than as a Dramatiq job, which **reverses**
  [backend.md](./backend.md) § Fetching pipeline's `extract_article` job row: the reader is
  blocked either way, and queueing would add a polling loop and a third state on screen for a
  slow path that runs once per post (measured: 0.99s first call, 0.012s second).
  `backend/core/extract.py` mirrors `ingest.py`'s shape — one network function, one entry point
  that never raises — and pipes trafilatura's HTML through `nh3.clean` with our own allowlist,
  because the frontend will render that field as markup and the guarantee has to be ours rather
  than a property of trafilatura's internals. The column keeps three states (`null` untried, `''`
  read-but-empty, the article) where the wire carries two (`ok` / `unavailable`), and **anything
  short of an article is retried on the next open** — `''` as much as `null` _(amended after
  T10, in the tree committed 2026-09-15; T10 itself cached the empty read)_: a bot-challenge page
  served as 200 or a site mid-deploy reads as empty once, and one bounded fetch per open is cheap
  next to a post that is wrong for every subscriber forever. The `''` is still stored so admin
  can tell "tried, empty" from "never tried". The fetch itself refuses non-public targets on every redirect hop, caps the body at
  2MB and rejects non-HTML, since unlike ingest this endpoint hands what it downloads back to the
  caller. Eight decisions — including that SSRF check's stated DNS-rebinding limit, the YouTube
  short-circuit, and why `favor_precision` is off — are in
  [backend-roadmap.md](./backend-roadmap.md) § Decision log (2026-09-05, T10).
  Verified: 208 backend tests green (was 182), `ruff check` clean, and driven against live pages —
  a blog post extracted in 0.99s and served from the column in 0.012s, a YouTube post answered
  `unavailable` in 0.010s with no outbound request, and Reddit's JS interstitial correctly stored
  as "read it, no article". **Nothing on the frontend calls the endpoint yet** — the reader still
  renders the stripped `summary` (see Not started → Post page (rest)), which is why nothing on
  screen changed.
  **T12 landed _(2026-09-06)_, ahead of T11a and on the server only:** `GET /search?q=&scope=`
  searches inside any list the app can already read — the `scope` is the *same* polymorphic uid
  the post list takes, resolved by the *same* `core/postlist.py` resolver, so muting a feed drops
  it from that folder's results immediately with no re-index, another user's uid 404s, and the
  response is byte-for-byte a post page paged by T5's cursor. `Post.search` is a **persisted
  generated tsvector** (title weighted over summary, `english`), recomputed by Postgres in the
  statement that writes the row, so search is never stale and there is no sync pipeline;
  migration `0004_post_search.py` installs `pg_trgm` by hand first (`makemigrations` never emits
  an extension operation), then the column, then a GIN index on it and a **functional** trigram
  index on `upper(title)` — functional because Django compiles `__icontains` to
  `UPPER("title"::text) LIKE …` and the planner only matches an index built on the same
  expression. Nothing was installed to do any of it: `pg_trgm` is a Postgres extension and
  `django.contrib.postgres` ships with Django. Matching is two branches: full-text (`websearch`,
  so a stray quote comes back empty instead of 500ing) over title and summary, plus a title-only
  substring for the partial words FTS structurally can't reach — `summary` is never
  substring-matched, since it is third-party HTML and that would match markup. Results are
  ordered by **recency, not relevance** (the weights are in the vector, so ranking later is an
  `order_by`, not a migration), and a blank `q` is an empty page rather than a 422. All of it
  lives in `backend/core/search.py`, with a **test that scans `core/` and fails** if any other
  module touches the tsvector column — which is what keeps
  [backend.md](./backend.md#search)'s "swap in Elasticsearch by rewriting one module" promise
  checkable. Nine decisions are in [backend-roadmap.md](./backend-roadmap.md) § Decision log
  (2026-09-06, T12). Verified: 255 backend tests green (231 before, 24 new), `ruff check` clean,
  and against the real dev database — partial words matching real posts, every scope branch,
  a mute reflected instantly, 105 results paged two at a time across 53 pages with no duplicates,
  and `openapi.json` carrying `search_posts` under `feeds` with still exactly four tags.
  **The frontend is wired to it** — the feed page and the desktop posts pane search from their
  title row (see Built → Feed page v1), and `app/types/api.d.ts` has been regenerated to carry
  the `/search` path.
  **T13 landed _(2026-09-07)_, with no endpoint and no screen behind it:** the posts table now has
  a ceiling. `backend/core/retention.py` holds every deletion rule — unsaved posts older than **90
  days**, and per source those beyond the newest **500**, both rules deleting, so a post goes if
  either catches it — and **a saved post is never deleted**, at any age and no matter who saved it,
  since a post row is global and an owner-scoped rule would empty another account's pile. The cap
  keeps its newest rows by excluding their pks rather than comparing against a boundary timestamp,
  which is what makes it exact when a source stamps a whole batch with the same second. Deletes run
  in batches of 1000 pks, and `--dry-run` is the real run inside a rolled-back transaction rather
  than a simulation, because the cap pass ranks whatever the age pass left behind. Two daily actors
  in `core/tasks.py` (03:30 and 03:45) wrap the plain functions the way `poll_source` wraps ingest,
  with `manage.py prune_posts --days --cap --dry-run` as the manual override; the second one,
  `prune_expired_tokens()`, deletes `AuthToken` rows past `core/auth.py`'s imported `TOKEN_TTL` and
  closes the forward reference T2 left. The one change outside the new module is that **ingest now
  respects retention's line**: `_upsert_posts` won't create a post the prune would delete that
  night, because the first live run watched an archive feed put 49 just-deleted posts straight back
  on the next five-minute sweep — the consequence being that a feed whose entries are all past the
  window subscribes successfully with zero posts. Nine decisions are in
  [backend-roadmap.md](./backend-roadmap.md) § Decision log (2026-09-07, T13). Verified: 285
  backend tests green (was 263, 22 new), `ruff check .` clean, and against the real dev database —
  a dry run that predicted 51 deletions and a real run that deleted exactly those 51, a saved
  200-day-old post surviving both, and the post list, the saved list and `/search` all correct
  afterwards.
  **Hardened alongside, in the same tree:** the writes now refuse what would have been a 500 or a
  silent truncation — a name with a NUL byte is a 422 (one `clean_name` shared by feed and folder
  writes, so the two can't disagree about what a name is), a `feed_url` past the column's 500
  characters is a 422 rather than a truncated fetch of a different URL, a double-tapped Subscribe
  that races past the exists-check is caught at the unique constraint and answered as the same
  "You already follow that feed.", an ingest that raises mid-subscribe deletes the new source
  row instead of leaving a dead one behind, and a brand-new source is created already claimed
  for the poll interval so the five-minute sweep can't poll it from the worker while the inline
  fetch is still running. `PATCH /folders/{uid}` is one transaction from the rename down, so a
  refused membership takes the rename back with it; `DELETE /me` deactivates every source the
  account was the last subscriber of, since the cascade is the one way feeds vanish without
  passing through unsubscribe; and a cursor carrying a naive timestamp is a 422. **316 backend
  tests green in the tree as committed** (T13's 285 plus T11b's 12 in `test_youtube.py` and the
  tests behind the hardening above), `ruff check .` clean.

- **Feed discovery** _(T11a, 2026-09-06)_ — the add wizard's search step does real work: paste a
  URL and `GET /discover` turns it into feeds you can subscribe to. **T11 was split into four**
  (see [backend-roadmap.md](./backend-roadmap.md) § Status); T11a is the part needing no external
  accounts, and T12 was built ahead of it. A pasted URL is fetched once and either parsed as a feed
  or read for the `<link rel="alternate">` tags it declares. Two shapes drove the design and both
  came from pasting real URLs, not from the suite, which was green throughout: **a post URL**
  (`nuxt.com/blog/meet-nuxi`) declares no feed while the section index above it does, so the
  resolver **walks up the path** — nearest first, always reaching the site root, capped at three
  fetches, and only when the pasted page came up empty; and **YouTube closes `<head>` after
  ~700 KB of inline script**, declaring its title and `videos.xml?channel_id=…` link in the *body*,
  so the parser reads the whole document (8 ms on a 1.6 MB page — `HTMLParser` skips script bodies
  as CDATA). Failing all that, `/feed`, `/rss`, `/rss.xml`, `/atom.xml`, `/index.xml` are probed at
  the root, which catches static-site generators that ship a feed and forget the tag. T10's
  SSRF-guarded fetch moved out of `core/extract.py` into **`core/fetch.py`**, shared by both
  callers that hand a fetched body back to the requester — a forced move, not a tidy-up: discovery
  needs a different accept header, content-type allowlist and byte cap, and once those are
  arguments the function is no longer "the article page fetcher". No new dependency: `feedparser`
  answers "is this a feed", stdlib `html.parser` answers "where is the feed on this page". Nine
  decisions are in [backend-roadmap.md](./backend-roadmap.md) § Decision log (2026-09-06, T11a).
  Verified: 263 backend tests green (28 new in `test_discover.py`, 17 in `test_fetch.py` of which
  15 moved with the code), `ruff check` / `pnpm lint` / `pnpm typecheck` clean, and against live
  sites — a Nuxt post URL, two feeds off overreacted.io, three off github.blog, Hacker News, two
  YouTube handles in ~450 ms, and `r/vuejs`. **Known limitation:** Reddit answers **429** to
  repeated unauthenticated `.rss` fetches, so a subreddit can resolve on one search and not the
  next; app credentials (T11c) are the fix.
  **T11b _(2026-09-11)_ — YouTube by name.** A bare name under the YouTube card is a Data API
  `search.list` (`backend/core/youtube.py`, the one module that spends quota; `fetch_search` is
  its one network call), mapped to the same `videos.xml` candidate a pasted channel resolves to,
  with the channel avatar as `icon_url`. Shaped by the quota — 10k units a day, 100 per search:
  every answer is **cached for a day** under a hashed, whitespace-and-case-normalised key, a
  failed search is not cached (an error would otherwise be served for a day), and at most five
  channels come back even when YouTube overshoots `maxResults` (seen live). Django's cache is
  now the same Redis the broker uses (`CACHES` in `settings.py`), with one standing rule —
  never `cache.clear()` against it, since on that backend it is `FLUSHDB` and the queues share
  the database; tests swap in locmem so they can. `YOUTUBE_API_KEY` is optional like the Google
  client id: without it a name finds nothing and a URL or `@handle` still resolves through the
  channel page, spending no quota either way. YouTube refusing to answer is a **503** ("YouTube
  search is unavailable right now."), never an empty list. Frontend: `SearchStep.vue` leads a
  YouTube row with its avatar (square by nature — a website's `icon_url` is as often a wide
  banner, so that gets its own pass) and shows the 503 as an error rather than "Nothing found".
  The card decides what a bare name means — `one piece` is a channel search under YouTube and
  nothing under Website — and a keyword under the other two cards is unchanged (T11c, T11d).

- **Routing scheme** _(2026-06-29)_ — **nested routes**: posts nest under feeds
  (`/feed/[uid]/post/[postUid]`), settings subpages nest under settings (`/settings/*`). The
  route encodes navigation context. Scaffold files (`Feed.vue`, `[Post].vue`,
  `SettingsAccount/About` components) move to match the nested tree. See
  [screens-and-flows.md](./screens-and-flows.md). **Amended _(2026-07-27)_:** the
  desktop two-pane presentation this route nesting was meant to drive is instead
  composed by the layout from these same routes (see "Desktop layout composition"
  above) — the routes stayed exactly as this decision specced, only the desktop
  *rendering mechanism* changed.
- **Saved posts entry point** _(2026-06-29)_ — saved posts surface as a **Saved** feed pinned
  in the feeds list (no `saved.vue` screen, no navbar bookmark icon). Saving stays the toggle
  on the Post page. Routed as `/feed/saved`, reusing the feed-page component.
- **Folders** _(2026-06-30)_ — feeds can be grouped into named **folders**, **many-to-many** (a
  feed can be in several folders; loose if in none). Created from the navbar **+** menu; edited
  via a long-press / 3-dot context menu (rename, add/remove feeds, **per-folder mute**, delete).
  **Mute** is per-folder only. **Remove from folder** unlinks; **delete feed** unsubscribes
  everywhere; **delete folder** also unsubscribes its feeds except those in another folder (with
  confirmation). See [data-model.md](./data-model.md#folder).
- **Saved groups** _(2026-07-11)_ — Saved is not one pile: saves organize into three fixed
  groups — **Bookmarks / Favorites / Later** (`app/utils/saved.ts`, uids `saved_*`). On the
  home list Saved is an expandable pinned row (tap → `/feed/saved`, all groups merged; expand →
  the three group rows → `/feed/saved_*`). Group uids resolve on the feed page before
  folder/feed uids. Saved groups are deliberately **not** store `Folder`s — that would leak
  them into the add-wizard destination list and the loose-feed computation.
- **Folder reads through the feed page** _(2026-07-01)_ — a folder is **not** its own route.
  The feed page (`/feed/[uid]`) is polymorphic: `uid` resolves in a fixed order — `saved` →
  folder (`folder_*`) → feed (`feed_*`) — exactly the pattern `saved` already established.
  Chosen over a separate `/folder/[uid]` tree to avoid duplicating the feed/post routes; the
  page stays thin by delegating to a `usePostList(uid)` resolver. If folders ever need
  folder-specific chrome, splitting out a dedicated route is a cheap, additive refactor. See
  [screens-and-flows.md](./screens-and-flows.md).
