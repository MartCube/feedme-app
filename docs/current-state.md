# Current State

A snapshot of what's actually built vs. what the spec (these docs) describes. The goal is to
make the gap visible so implementation has a clear backlog. Update this as work lands.

_Last reviewed: 2026-09-01._

## Summary

The **design system** and **navigation/drawer UX** are well developed, and the three **reader
screens** (feeds list, feed page, post page) navigate end to end. **Desktop
(≥1024px) v1** now renders those same screens as a three-column shell — sidebar, posts pane,
post pane — composed by the layout from the same routes and store state; Settings/Add/Edit
present as full content pages over the reading panes instead of drawers. **The app runs on real
data** _(2026-09-01)_: a `/login` screen takes a dev token, and the account's own feeds,
folders, fetched posts, saved posts and settings all come from the Django API in `backend/`
(Django + django-ninja, Docker Compose) — the mock data files are deleted and nothing falls
back to them. What has no endpoint behind it yet says so: the add wizard's search finds nothing,
and every add/edit write is still store-local. See Resolved decisions → Backend stack & API.
Backend work is sequenced in [backend-roadmap.md](./backend-roadmap.md), which tracks its
own status: **read that file's § Status for what to build next.**

## Built

- **Theme tokens** — 9 `--ui-*` color roles themed in `app/assets/css/themes.css` (two dark
  themes: Ink default + Claude; the old teal/ink/silver ramps are removed), plus the 4-size
  type scale (`text-title/subtitle/body/caption`) and `shadow-elevated`. The font family and
  type scale live in their own `app/assets/css/typography.css` (imported by `main.css`), and the
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
  Committing calls `useFeedsStore().addFeed()` per picked feed and the home list updates (still
  store-local — `POST /feeds` is T7). The search itself **finds nothing** until T11's
  `/discover`: the step keeps its real shape (query in, loading flag, candidates out) and says
  "Nothing found — searching for feeds isn't wired up yet" once a search has actually been run.
- **Edit-feed / edit-source drawer** — `app/components/edit/Drawer.vue` hosts the sheet (UDrawer
  + open protocol + close-key provide + animation-end navigation), like the settings/add
  drawers; every `/edit/*` URL renders the home component (`pages:extend`) so the list stays
  behind the sheet on mobile. The route-driven panel switch and confirm-descriptor table live in
  `app/components/edit/Panels.vue` (`EditPanels`), shared by the mobile drawer and, on desktop,
  the content overlay. Opened by **long-press** on a folder or loose-feed home
  row (mobile, `useLongPress` — suppresses the follow-up nav click) or a **hover-revealed 3-dot**
  on the row (desktop only, `@media (hover: hover)`). Polymorphic by uid: a `folder_*` uid opens
  the **folder panel** (`edit/FolderPanel.vue` — rename input + a **Save** pill, a "Sources"
  list of member feeds each row spanning the full drawer width with an on/off mute toggle
  (`ui/Toggle.vue`), a dashed full-width ghost row labelled "Add source" that runs the add
  wizard scoped to this folder — skipping the destination step and returning here — and a
  `ui/DangerButton.vue` labelled "Delete feed"); a loose `feed_*` uid opens the **source panel**
  directly (`edit/SourcePanel.vue` — edits the **name only**, with the RSS `feed_url` shown as
  read-only text below it (it lives on the shared global `Source`; [backend-roadmap.md](./backend-roadmap.md)
  § Contract resolutions, 3), back caret + `useSwipeBack`
  when reached as a folder member (`/edit/:uid/source/:sourceUid`), X close when standalone; its
  `DangerButton` reads "Remove source from feed" as a member or "Delete source" standalone).
  Both the name and, in the folder panel, each source's mute toggle are staged as **local
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
  standalone feed when `:uid` is a loose `feed_*`, branching on the prefix) and the new
  `/edit/:uid/source/:sourceUid/delete` (route name `edit-source-delete`, registered in
  `nuxt.config.ts` `pages:extend`) which unlinks a member feed from the folder. Confirm/Cancel on
  the sheet itself are `ui/BlockButton.vue`. Row content in both panels is inset `sm` as real
  padding on the row (`pl-sm` on the link, `pr-sm` on the `li`) rather than a `text-inset` margin
  on the list, so row text lines up with the Name input, the RSS URL text, and the section
  headings.
  Panels slide with the shared `panel-slide` classes. Backing `feeds`-store actions:
  `renameFolder`, `setMutedFeeds` (replaces the folder's whole muted set in one immutable
  write — the folder panel's draft toggles it once, on Save), `updateFeed`, `removeFromFolder`,
  `deleteFeed`, `folderDeleteImpact`, `deleteFolder`.
  **Copy diverges from the agreed screen 7 wording** (see
  [screens-and-flows.md](./screens-and-flows.md#7-create--edit-folders--feeds-from-the-home-list)):
  spec calls the actions "Delete folder" / "Delete feed" / "Remove from this folder"; shipped
  labels are "Delete feed" for deleting the *folder*, "Delete source" for deleting a standalone
  *feed*, and "Remove source from feed" for unlinking a *feed* from a *folder* — a
  Source/Feed/Folder vocabulary swap against [backend.md](./backend.md)'s vocabulary table that
  hasn't been reconciled either way.
- **Layouts** — `app/layouts/default.vue` is the single layout and the mobile/desktop branch
  point: `useIsDesktop()` (`app/composables/useIsDesktop.ts` — VueUse `useMediaQuery` at the
  `lg` 1024px tier, gated behind `useMounted` so SSR and the hydration render always emit the
  mobile tree, flipping only after mount on wide clients) chooses between the unchanged mobile
  tree (`lg:hidden`-masked for a wide first paint, hosting the three drawers) and
  `DesktopShell`. `isDesktopNow()` is the synchronous twin for imperative guards.
- **Desktop shell v1** (`app/components/desktop/`) — ≥1024px renders three columns composed
  straight from the route and the `feeds` store, not a nested-route tree: `Sidebar.vue` (18rem)
  — two collapsible sections, expansion persisted in the `settings` store
  (`sidebarFeedsOpen`/`sidebarSettingsOpen`) — **Feeds** (the shared `HomeFeedList` plus an
  "Add feed" row → `/add`) and **Settings** (rows from `settingsSections`, active by path); a
  posts pane (24rem, `FeedPostList`); and a post pane (flexible, capped at a 42rem reading
  measure, `FeedPostView`, or a dimmed "Select a post" placeholder — **no auto-select**).
  `Shell.vue` reads `useRouter().currentRoute` rather than Nuxt's `useRoute()` (Nuxt's route
  object only resyncs when a `NuxtPage` resolves, and the shell renders none), syncing the
  feeds store's `readerFeedUid`/`readerPostUid`/`readerPath` on reader routes only — they stay
  frozen while a content route is open. Settings, Add, and Edit present as a full opaque
  overlay (`ContentOverlay.vue`) over the two reading panes: the sidebar stays interactive, the
  reading panes stay mounted underneath (feed, selected post, and pane scroll all survive a
  round-trip), and closing returns to the frozen reader path; it's left-aligned (not centered)
  so its `page-inset` lines up with the sidebar's. The overlay reuses the exact
  mobile panel components (`app/utils/settings-panels.ts`'s route map, `AddSteps`,
  `EditPanels`) and resets the add wizard on any exit from `/add` or `/edit/*`. The three drawer
  hosts guard their `onMounted` open-on-deep-load with `isDesktopNow()` so a desktop deep-load
  of `/settings/*`, `/add`, or `/edit/*` never flashes a bottom sheet. Layout tokens live in
  `app/assets/css/layout.css` (`--container-sidebar/postlist/reading/shell`, a `@theme static`
  block in its own namespace so it doesn't collide with the six-name `--spacing-*` rule) —
  `--container-shell` (100rem) centers and caps the whole shell on large monitors. **v1 is
  deliberately unpolished:** no desktop transitions, keyboard focus rings still suppressed, and
  `HomeOptionsDrawer` still opens as a bottom sheet on desktop — all queued for a later
  design/polish pass.
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
  field breaks typecheck instead of silently rendering blank. `FeedCandidate` stays hand-written
  until T11's `/discover` gives it a schema.
- **Auth & login** — `app/pages/login.vue` (brand, one line, one field: a **dev token** until
  T8's Google button; `definePageMeta({ layout: false })` is load-bearing, since the default
  layout renders `DesktopShell` instead of the page above 1024px). `app/stores/auth.ts` holds
  the token (cookie-persisted, `pick: ['token']` only) and the `/me` profile; `signIn()` proves
  a token against `/me` before keeping it, so a bad token fails on the login screen instead of
  as a redirect loop. `app/middleware/auth.global.ts` is a **pure guard** — everything except
  `/login` needs a token, and it does no fetching (see Resolved decisions → Backend stack & API
  → T6). Sign out (Settings → Account) revokes the token server-side via `POST /auth/logout`,
  clears both stores, and returns to `/login`.
- **Data layer** — the `feeds` store loads `GET /home` once (in-flight-guarded; a failure is
  swallowed rather than raised, so it can never surface as Nuxt's error page, and retries from
  the home screen's **Try again** or the next app boot) into feeds, folders and `savedCounts`,
  behind a `loaded` gate and an `unreachable` flag; the response's `order` is applied as a sort at load time and not retained
  (the list renders as folders-then-loose-feeds; interleaving is T7's drag-and-drop).
  `app/composables/usePostList.ts` cursor-pages `GET /feeds/{uid}/posts` (limit 10) behind a
  sentinel + VueUse `useIntersectionObserver` rooted on the viewport, so the same composable
  serves the mobile page scroll and the desktop pane. `app/composables/usePost.ts` owns one post
  plus its save toggle. The `settings` store loads `GET /settings` and `PUT`s on change (a full
  replace; `sidebarSettingsOpen` stays device-local and is never synced). Both loads run from
  `app.vue`'s `onMounted` (and again on sign-in), never from middleware — see Resolved decisions.
- **Feeds list v1** — `app/components/home/FeedList.vue` (`HomeFeedList`) renders the home list
  from the `feeds` store's `/home` load — used by the mobile home page (`app/pages/index.vue`)
  and, on desktop, the
  sidebar (an `activeUid` prop drives the desktop persistent-selection highlight): a pinned
  **Saved** row (links to `/feed/saved`; chevron expands to the three saved groups —
  Bookmarks / Favorites / Later from `app/utils/saved.ts`, each → `/feed/saved_*`, each showing
  its count from `/home`'s `saved_counts`, the same muted count a folder row carries), then
  folder rows (name + feed count, expand/collapse chevron with auto-animate and an accent tap
  flash, sitting **inside** the row's tap-flash card surface at IconButton size on the navbar
  buttons' vertical axis; members indented and greyed when muted), then loose feeds; every row
  links to `/feed/[uid]`. Chevrons point **right** when collapsed and rotate to down when
  expanded. Above the list, **Home** is itself a list row (same surface, tap flash, and cards
  treatment as the rest) at title size with an **All feeds** caption, linking to `/feed/all`
  (the merged all-feeds read); its trailing 3-dot — sitting where folder rows keep their
  chevron, directly below the navbar **+** — opens a **half-height options sheet**
  (`app/components/home/OptionsDrawer.vue`, local-state drawer — not route-driven — with
  placeholder rows: New folder / Edit feeds / Reorder feeds). Names only for now — no type
  icons. Long-press (mobile) / hover 3-dot (desktop) on a folder or loose-feed row opens the
  **edit-feed / edit-source drawer** (see Built, below).
- **Feed page v1** — `app/components/feed/PostList.vue` (`FeedPostList`, `uid` + `activePostUid`
  props) lists PostCards with the resolved feed/folder name as title — used by the mobile feed
  page (`app/pages/feed/[uid]/index.vue`) and, on desktop, the shell's posts pane. Posts come
  from `usePostList(uid)` — the uid resolves **server-side** in the frontend's own order
  (`all` → `saved` → `saved_*` → `folder_*` → `feed_*`), so the component filters nothing and
  just renders what pages in; a uid change resets the list rather than appending. The list says
  "No posts here yet" when a stream is genuinely empty and "Couldn't load posts." when a page
  request failed (paging stops rather than retrying into a refusing server).
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
  (`app/utils/strip-html.ts`) — nothing sanitises third-party markup, and T10's extracted
  article text is the real answer. Open source is still missing on both viewports.
- **PostCard v1** — `app/components/feed/PostCard.vue`: date + title only (no image / type cue
  yet), whole card links to the post; rows separated by spacing (no divider lines).
- **Context-aware navbar** — both slots swap per page: home = menu + add, feed page =
  sidebar icon (→ home) + search (no-op for now), post page = back (→ its feed) + save
  (wired — see Post page v1). Navigation is hierarchical, not history-based.
- **Reader slide transitions** — **mobile only** (the desktop shell renders no `<NuxtPage/>`,
  so this machinery never runs there — see Desktop shell v1). home → feed → post slide like a
  navigation stack (deeper pushes in from the right, back pops out to the right). Direction is
  set on route meta by `app/middleware/page-slide.global.ts` (computed *before* render — a
  component watch is one navigation late), shared `.page-slide-*` classes live in
  `assets/css/transitions.css`, and the default layout provides the positioning/clip context.
  Non-reader routes (add, settings) swap instantly (`page-none`) so their drawer animations own
  the motion; the settings drawer's internal slides reuse the same CSS classes via
  `usePageSlide()`.
- **Swipe navigation** — `app/composables/useSwipeNav.ts` (VueUse `useSwipe`, touch-only).
  `useSwipeBack`: swipe right anywhere on the feed page, post page, a settings subpage, or an
  edit-source subpage drags the page with the finger and past 72px pops to the parent route
  (reusing the page-slide / panel-slide pop); under threshold it snaps back. `useSwipeOpen`: swipe left
  on a home feed row or settings section row nudges it and opens it (gesture twin of
  tapping; one delegated listener per list). Axis-locked so vertical scrolling and vaul's
  drag-to-close are untouched; back buttons unchanged.

## Stubs (exist but placeholder content)

- **Add-feed search** — the wizard flow, add action, and destination picker are built (see
  Built), but no search backs them: the step reports "Nothing found" until T11's `/discover`.

## Not started

- **Post page (rest)** — Open source, and the **article text** itself: the reader shows the RSS
  `summary` as plain text until T10's `/posts/{uid}/article`.
- **Desktop polish** — v1 (see Built → Desktop shell v1) ships the structural three columns
  only: no desktop pane/overlay transitions, keyboard focus rings still globally suppressed,
  and `HomeOptionsDrawer` still opens as a mobile-style bottom sheet on desktop. The post pane
  has **no action bar**, so the save toggle is mobile-only. Auto-selecting
  a detail post (e.g. the last-read one) on entering a feed is also deferred — v1 always starts
  at the "Select a post" placeholder.
- **Settings content** — the drawer, its four subpages, and transitions are built, and
  Appearance and Account are real (see Built); About's version string is hardcoded and Report
  still needs real content and a way to actually send anything.
- **PostCard (rest)** — image and source-feed type cue.
- **Add feed (rest)** — real search / RSS discovery + live metadata (sub counts, latest items)
  behind the wizard, subscribing for real (`POST /feeds`, T7 — `addFeed` is still store-local),
  and input validation via VeeValidate/Zod. The wizard UI + add action are built (see Built).
- **Saved posts (rest)** — saving, unsaving and reading the saved streams work end to end (see
  Built), but every save lands in **Bookmarks**: there is no group chooser and no way to move a
  post between Bookmarks / Favorites / Later, though the API call for it is the same upsert.
- **Folders (rest)** — the expandable rows on the home list, the merged-stream read, **folder
  creation inside the add wizard** (`addFolder` store action + `add/FolderStep.vue`), and the
  **edit-feed / edit-source drawer** (see Built) are done. Still missing: the folder writes
  themselves (`POST`/`PATCH`/`DELETE /folders`, T7 — rename, membership, mute and delete are
  store-local) and the actions behind the home options sheet
  (New folder / Edit feeds / Reorder feeds are still placeholder rows). See
  [data-model.md](./data-model.md#folder) and
  [screens-and-flows.md](./screens-and-flows.md).
- **Writes (rest)** — reads are wired end to end; every **write** except save and settings is
  still store-local: subscribing, renaming, folder membership, mute, delete, and the home
  reorder all wait on T7's endpoints.

## Installed but unused

- **VeeValidate + Zod** — not wired into any form yet.
- **@vueuse/motion** — available for animations.

## Open decisions

_None currently._

## Resolved decisions

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
  `worker`/`scheduler` are deliberately deferred until Dramatiq lands. `.env.example` is at
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
