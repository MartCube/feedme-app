# Current State

A snapshot of what's actually built vs. what the spec (these docs) describes. The goal is to
make the gap visible so implementation has a clear backlog. Update this as work lands.

_Last reviewed: 2026-07-11._

## Summary

The **design system** and **navigation/drawer UX** are well developed, and the three **reader
screens** (feeds list, feed page, post page) now navigate end to end on mock data. There is
**no data layer** (no RSS fetching, no persistence beyond the theme setting). The app runs
entirely on static mock data in `app/assets/data.ts`, served through the `feeds` store.

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
- **Navbar** — `app/components/Navbar.vue` (menu → `/settings`, add → `/add`).
- **IconButton** — `app/components/ui/IconButton.vue` (round soft-fill button, accent press
  flash). A `quiet` variant blends into the page bg at rest and lifts to the normal
  elevated look while the press flash runs (home 3-dot options trigger).
- **Settings drawer** — `app/components/settings/Drawer.vue` hosted in the layout; the
  `/settings/:panel?` route renders the home component (via `pages:extend`) so the feed list
  stays behind the sheet, and panels swap as in-drawer components with `panel-slide`
  transitions. Main page (`settings/Home.vue`): in-flow close → title → section list with the
  shared tap-selection flash (row + leading icon accent flash). Subpages (Account / Appearance
  / About / Report) share `settings/Page.vue`: back + the section's own muted icon + `text-subtitle`
  title as a where-am-I cue (sections defined once in `app/utils/settings-drawer.ts`). Appearance is
  functional (theme switch); the rest are mock content.
- **Add-feed wizard** — `app/components/add/Drawer.vue`, hosted in the layout like the settings
  drawer. The `/add` URL renders the home component (via the `pages:extend` hook) so the feed
  list stays behind the sheet; the navbar **+** links straight to `/add` (no dropdown), and
  close routes back to `/`. Inside, a four-phase in-drawer wizard (state in
  `useAddFeedWizard()`): **pick type** (`add/TypeStep.vue`, cards with an accent caret tap flash) →
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
- **Layouts** — `app/layouts/default.vue` (centered column + Navbar), `plain.vue` (bare).
- **Mock data & types** — `app/assets/data.ts` (3 feeds, 1 folder, 15 posts),
  `app/assets/types.ts` (incl. the `Folder` type).
- **Feeds list v1** — `app/pages/index.vue` renders the home list from mock data: a pinned
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
  icons, no context menus yet.
- **Feed page v1** — `app/pages/feed/[uid]/index.vue` lists PostCards with the resolved
  feed/folder name as title. **Temporary:** every uid shows all posts from all feeds, newest
  first — the `usePostList(uid)` resolver comes with the data layer. `[uid].vue` is a
  `<NuxtPage/>` passthrough until the desktop master/detail layout lands.
- **Post page v1** — `app/pages/feed/[uid]/post/[postUid].vue` renders title, date, content
  (no Save / Open source yet).
- **PostCard v1** — `app/components/feed/PostCard.vue`: date + title only (no image / type cue
  yet), whole card links to the post; rows separated by spacing (no divider lines).
- **Context-aware navbar** — both slots swap per page: home = menu + add, feed page =
  sidebar icon (→ home) + search (no-op for now), post page = back (→ its feed) + save
  (no-op for now). Navigation is hierarchical, not history-based.
- **Reader slide transitions** — home → feed → post slide like a navigation stack (deeper
  pushes in from the right, back pops out to the right). Direction is set on route meta by
  `app/middleware/page-slide.global.ts` (computed *before* render — a component watch is one
  navigation late), shared `.page-slide-*` classes live in `assets/css/transitions.css`, and the
  default layout provides the positioning/clip context. Non-reader routes (add, settings)
  swap instantly (`page-none`) so their drawer animations own the motion; the settings
  drawer's internal slides reuse the same CSS classes via `usePageSlide()`.
- **Swipe navigation** — `app/composables/useSwipeNav.ts` (VueUse `useSwipe`, touch-only).
  `useSwipeBack`: swipe right anywhere on the feed page, post page, or a settings subpage
  drags the page with the finger and past 72px pops to the parent route (reusing the
  page-slide / panel-slide pop); under threshold it snaps back. `useSwipeOpen`: swipe left
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
- **Master/detail layout** — single pane on mobile, two panes (feed list + post / settings nav
  + subpage) on desktop, off the same nested routes.
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
  home list, and **folder creation inside the add wizard** (`addFolder` store action +
  `add/FolderStep.vue`) are done (see Built). Still missing: the folder merged-stream read
  (`/feed/[uid]` with a folder uid, via the `usePostList(uid)` resolver), the actions behind
  the home options sheet (New folder / Edit feeds / Reorder feeds are placeholder rows), and
  an edit context menu (long-press / 3-dot) for
  rename, add/remove feeds, per-folder mute, and delete, plus a folders store. See
  [data-model.md](./data-model.md#folder-new--not-yet-in-code) and
  [screens-and-flows.md](./screens-and-flows.md).
- **State layer (rest)** — the `feeds` store exists but is mock-seeded; still missing: saved
  state and wiring to real data.
- **Data fetching / RSS** — no `server/` routes, no `$fetch`/`useAsyncData`, no parser. All
  data is static. The fetching + persistence stack is undecided (to be specced separately).

## Installed but unused

- **VeeValidate + Zod** — not wired into any form yet.
- **@vueuse/motion** — available for animations.

## Open decisions

_None currently._

## Resolved decisions

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
  Nothing is implemented yet — the spec is the agreed target.

- **Routing scheme** _(2026-06-29)_ — **nested routes**: posts nest under feeds
  (`/feed/[uid]/post/[postUid]`), settings subpages nest under settings (`/settings/*`). The
  route encodes navigation context and drives a master/detail layout (one pane on mobile, two
  on desktop). Scaffold files (`Feed.vue`, `[Post].vue`, `SettingsAccount/About` components)
  move to match the nested tree. See [screens-and-flows.md](./screens-and-flows.md).
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
