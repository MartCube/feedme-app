# Current State

A snapshot of what's actually built vs. what the spec (these docs) describes. The goal is to
make the gap visible so implementation has a clear backlog. Update this as work lands.

_Last reviewed: 2026-07-10._

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
  `app/assets/css/spacing.css`. See [design-system.md](./design-system.md).
- **Theme switch** — Settings → Appearance picks Ink or Claude via the persisted Pinia
  `settings` store (`pinia-plugin-persistedstate`, cookie);
  `app.vue` applies `data-theme` on `<html>` via `useHead`.
- **Navbar** — `app/components/Navbar.vue` (menu → `/settings`, add → `/add`).
- **IconButton** — `app/components/ui/IconButton.vue` (round soft-fill button, accent press
  flash).
- **Settings drawer** — `app/components/settings/Drawer.vue` hosted in the layout; the
  `/settings/:panel?` route renders the home component (via `pages:extend`) so the feed list
  stays behind the sheet, and panels swap as in-drawer components with `panel-slide`
  transitions. Main page (`settings/Home.vue`): in-flow close → title → section list with the
  shared tap-selection flash. Subpages (Account / Appearance / About / Report) share
  `settings/Page.vue`: back + `text-subtitle` title + the section's own muted icon far right
  as a where-am-I cue (sections defined once in `app/utils/settings-drawer.ts`). Appearance is
  functional (theme switch); the rest are mock content.
- **Add-feed wizard** — `app/components/add/Drawer.vue`, hosted in the layout like the settings
  drawer. The `/add` URL renders the home component (via the `pages:extend` hook) so the feed
  list stays behind the sheet; the navbar **+** links straight to `/add` (no dropdown), and
  close routes back to `/`. Inside, a three-phase in-drawer wizard (state in
  `useAddFeedWizard()`): **pick type** (`add/TypeStep.vue`) → **paste/search** with a Paste chip,
  ~1s skeleton, and mock results (`add/SearchStep.vue`) → **choose destination** — top level or a
  folder (`add/DestinationStep.vue`). Phases slide with the `panel-slide` classes in
  `transitions.css`. Headers follow the settings drawer's language: step 1 has an in-flow close
  above the title; steps 2/3 have a md caret back + `text-subtitle` title (no close). The search
  input is enlarged for mobile (taller padding, `text-body`, `rounded-2xl`). Destination rows
  flash on tap and **commit via a trailing plus button** (prep for many-to-many multi-select).
  Committing calls `useFeedsStore().addFeed()` and the home list updates. Results are a mock
  (`app/assets/mock-search.ts`, fixed per-type, query ignored); real search/RSS is not wired.
  Below the type list sit two **inert folder-CTA variants** ("New folder" / "Edit folders" —
  elevated blocks vs. quiet rows) awaiting a pick; the loser gets deleted.
- **Layouts** — `app/layouts/default.vue` (centered column + Navbar), `plain.vue` (bare).
- **Mock data & types** — `app/assets/data.ts` (3 feeds, 1 folder, 15 posts),
  `app/assets/types.ts` (incl. the `Folder` type).
- **Feeds list v1** — `app/pages/index.vue` renders the home list from mock data: folder rows
  (name + feed count, expand/collapse chevron with auto-animate, members indented and greyed
  when muted) above loose feeds; every row links to `/feed/[uid]` (folder uid included).
  Names only for now — no type icons, no Saved row, no context menus yet.
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

## Stubs (exist but placeholder content)

- **Add-feed search** — the wizard flow, add action, and destination picker are built (see
  Built), but results come from a fixed mock (`mockSearch`), not real search/RSS discovery.

## Not started

- **Feed page (rest)** — the `usePostList(uid)` resolver (saved → folder → feed, per-feed
  filtering, folder mute). Includes `/feed/saved`.
- **Post page (rest)** — Save + Open source actions.
- **Master/detail layout** — single pane on mobile, two panes (feed list + post / settings nav
  + subpage) on desktop, off the same nested routes.
- **Settings content** — the drawer, its four subpages, and transitions are built (see Built);
  Account / About / Report still need real content and actions behind their mock panels.
- **PostCard (rest)** — image and source-feed type cue.
- **Add feed (rest)** — real search / RSS discovery + live metadata (sub counts, latest items)
  behind the wizard, and input validation via VeeValidate/Zod. The wizard UI + mock + add action
  are built (see Built).
- **Saved posts** — a **Saved** feed pinned in the feeds list (no separate screen, no navbar
  icon) that lists all saved posts; plus the saved state itself.
- **Folders (rest)** — the `Folder` type, one mock folder, and the expandable rows on the
  home list are done (see Built). Still missing: the folder merged-stream read (`/feed/[uid]`
  with a folder uid, via the `usePostList(uid)` resolver), the **New folder / Edit folders**
  flows (two inert entry-point variants now sit below the Add drawer's type list awaiting a
  design pick; the wizard-like flows behind them are unbuilt),
  a New-folder drawer, an edit context menu (long-press / 3-dot) for
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

1. **Fetching + persistence stack** — how RSS is fetched (Nitro server route + parser?) and
   how feeds/saved state persist (local storage first, backend later?). To be specced when
   we move past mock data.

## Resolved decisions

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
- **Folder reads through the feed page** _(2026-07-01)_ — a folder is **not** its own route.
  The feed page (`/feed/[uid]`) is polymorphic: `uid` resolves in a fixed order — `saved` →
  folder (`folder_*`) → feed (`feed_*`) — exactly the pattern `saved` already established.
  Chosen over a separate `/folder/[uid]` tree to avoid duplicating the feed/post routes; the
  page stays thin by delegating to a `usePostList(uid)` resolver. If folders ever need
  folder-specific chrome, splitting out a dedicated route is a cheap, additive refactor. See
  [screens-and-flows.md](./screens-and-flows.md).
