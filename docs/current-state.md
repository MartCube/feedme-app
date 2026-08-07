# Current State

A snapshot of what's actually built vs. what the spec (these docs) describes. The goal is to
make the gap visible so implementation has a clear backlog. Update this as work lands.

_Last reviewed: 2026-08-07._

## Summary

The **design system** and **navigation/drawer UX** are well developed, and the three **reader
screens** (feeds list, feed page, post page) now navigate end to end on mock data. **Desktop
(≥1024px) v1** now renders those same screens as a three-column shell — sidebar, posts pane,
post pane — composed by the layout from the same routes and store state; Settings/Add/Edit
present as full content pages over the reading panes instead of drawers. There is **no data
layer** (no RSS fetching, no persistence beyond a handful of appearance settings — theme,
feed-list style, scrollbar style — and the two sidebar-expansion flags). The app runs entirely
on static mock data in `app/assets/data.ts`, served through the `feeds` store. A **backend
scaffold** now exists in `backend/` (Django + django-ninja, Docker Compose) — see Resolved
decisions → Backend stack & API — but the frontend isn't wired to it yet.

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
  `settings` store (`pinia-plugin-persistedstate`, cookie);
  `app.vue` applies `data-theme` on `<html>` via `useHead`.
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
  below). Appearance is functional (theme switch); the rest are mock content.
- **Add-feed wizard** — `app/components/add/Drawer.vue` hosts the sheet, like the settings
  drawer. The `/add` URL renders the home component (via the `pages:extend` hook) so the feed
  list stays behind the sheet on mobile; the navbar **+** links straight to `/add` (no dropdown),
  and close routes back to `/`. The four-phase slide switch itself lives in
  `app/components/add/Steps.vue` (`AddSteps`, emits `close`/`done` — the host decides what those
  mean, which is what lets the desktop content overlay reuse it), state in
  `useAddFeedWizard()`: **pick type** (`add/TypeStep.vue`, cards with an accent caret tap flash) →
  **paste/search** with a Paste chip, ~1s skeleton, and mock results as **multi-select cards**
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
  Committing calls `useFeedsStore().addFeed()` per picked feed and the home list updates. Results
  are a mock (`app/assets/mock-search.ts`, fixed per-type, query ignored); real search/RSS is not
  wired.
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
  directly (`edit/SourcePanel.vue` — edits name + RSS `feed_url`, back caret + `useSwipeBack`
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
  on the list, so row text lines up with the Name/RSS-URL input text and the section headings.
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
- **First-run empty state** — `app/components/home/EmptyState.vue` ("Nothing here yet" + an
  explainer + a primary "Add your first feed" action → `/add`), driven by the `feeds` store's
  `hasFeeds` computed (feeds or folders non-empty). Shown on the mobile home page in place of
  the list, and on desktop in place of both reading panes (the sidebar keeps working, so Add
  feed stays reachable). New spec surface — nothing was specced for the zero-feeds state
  before.
- **Mock data & types** — `app/assets/data.ts` (3 feeds, 1 folder, 15 posts),
  `app/assets/types.ts` (incl. the `Folder` type).
- **Feeds list v1** — `app/components/home/FeedList.vue` (`HomeFeedList`) renders the home list
  from mock data — used by the mobile home page (`app/pages/index.vue`) and, on desktop, the
  sidebar (an `activeUid` prop drives the desktop persistent-selection highlight): a pinned
  **Saved** row (links to `/feed/saved`; chevron expands to the three saved groups —
  Bookmarks / Favorites / Later from `app/utils/saved.ts`, each → `/feed/saved_*`), then
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
  page (`app/pages/feed/[uid]/index.vue`) and, on desktop, the shell's posts pane.
  **Temporary:** every uid shows all posts from all feeds, newest first — the `usePostList(uid)`
  resolver comes with the data layer. `feed/[uid].vue` stays a `<NuxtPage/>` passthrough on
  mobile; on desktop the shell bypasses it (and every route's `<NuxtPage/>`) entirely, composing
  the posts/post panes itself from the feeds store.
- **Post page v1** — `app/components/feed/PostView.vue` (`FeedPostView`, `postUid` prop) renders
  title, date, content (no Save / Open source yet) — used by the mobile post page
  (`app/pages/feed/[uid]/post/[postUid].vue`) and, on desktop, the shell's post pane.
- **PostCard v1** — `app/components/feed/PostCard.vue`: date + title only (no image / type cue
  yet), whole card links to the post; rows separated by spacing (no divider lines).
- **Context-aware navbar** — both slots swap per page: home = menu + add, feed page =
  sidebar icon (→ home) + search (no-op for now), post page = back (→ its feed) + save
  (no-op for now). Navigation is hierarchical, not history-based.
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
  Built), but results come from a fixed mock (`mockSearch`), not real search/RSS discovery.

## Not started

- **Feed page (rest)** — the `usePostList(uid)` resolver (all → saved → folder → feed,
  per-feed filtering, folder mute). Includes `/feed/all`, `/feed/saved`, and the
  `/feed/saved_*` groups (titles already resolve; the post list is still the
  show-everything mock).
- **Post page (rest)** — Save + Open source actions.
- **Desktop polish** — v1 (see Built → Desktop shell v1) ships the structural three columns
  only: no desktop pane/overlay transitions, keyboard focus rings still globally suppressed,
  and `HomeOptionsDrawer` still opens as a mobile-style bottom sheet on desktop. Auto-selecting
  a detail post (e.g. the last-read one) on entering a feed is also deferred — v1 always starts
  at the "Select a post" placeholder.
- **Settings content** — the drawer, its four subpages, and transitions are built (see Built);
  Account / About / Report still need real content and actions behind their mock panels.
- **PostCard (rest)** — image and source-feed type cue.
- **Add feed (rest)** — real search / RSS discovery + live metadata (sub counts, latest items)
  behind the wizard, and input validation via VeeValidate/Zod. The wizard UI + mock + add action
  are built (see Built).
- **Saved posts** — the pinned **Saved** row + its three group rows are built on the home
  list (see Built), but the saved state itself (which posts are saved, into which group) and
  the Post-page save action are missing — every saved route still shows the all-posts mock.
- **Folders (rest)** — the `Folder` type, one mock folder, the expandable rows on the
  home list, **folder creation inside the add wizard** (`addFolder` store action +
  `add/FolderStep.vue`), and the **edit-feed / edit-source drawer** (see Built) are done.
  Still missing: the folder merged-stream read (`/feed/[uid]` with a folder uid, via the
  `usePostList(uid)` resolver) and the actions behind the home options sheet
  (New folder / Edit feeds / Reorder feeds are still placeholder rows). See
  [data-model.md](./data-model.md#folder-new--not-yet-in-code) and
  [screens-and-flows.md](./screens-and-flows.md).
- **State layer (rest)** — the `feeds` store exists but is mock-seeded; still missing: saved
  state and wiring to real data.
- **Data fetching / RSS** — no `server/` routes, no `$fetch`/`useAsyncData`, no parser. All
  data is static. The fetching + persistence stack is specced ([backend.md](./backend.md);
  see Resolved decisions → Backend stack & API) and a hello-world scaffold now runs in
  `backend/`, but the frontend isn't wired to it — nothing beyond the mock data layer exists
  on this side yet.

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
  `/admin/` (no superuser yet). `docker-compose.yml` at the repo root runs `api` (port
  8000, code bind-mounted), `db` (Postgres 16, healthchecked, `pgdata` volume), and `redis`;
  `worker`/`scheduler` are deliberately deferred until Dramatiq lands. `.env.example` is at
  the repo root. Migrations run, the stack is verified. No models, auth, or endpoints
  beyond health exist yet — everything else `backend.md` specs is still the agreed target,
  not built.

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
  confirmation). See [data-model.md](./data-model.md#folder-new--not-yet-in-code).
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
