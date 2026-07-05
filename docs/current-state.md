# Current State

A snapshot of what's actually built vs. what the spec (these docs) describes. The goal is to
make the gap visible so implementation has a clear backlog. Update this as work lands.

_Last reviewed: 2026-07-03._

## Summary

The **design system** and **navigation/drawer UX** are well developed, and the three **reader
screens** (feeds list, feed page, post page) now navigate end to end on mock data. There is
**no data layer** (no RSS fetching, no store, no persistence). The app runs entirely on static
mock data in `app/assets/data.ts`.

## Built

- **Design system** — `app/pages/design.vue` (typography, colors, surfaces, borders, cards,
  avatars, dropdowns, collapsibles, form controls, button/icon-button variants, color
  ramps). The most complete file in the project.
- **Theme tokens** — `app/assets/css/main.css` (teal / ink / silver, Sora font) and
  `app/app.config.ts` (Nuxt UI theme overrides). Dark mode forced in `nuxt.config.ts`.
- **Navbar** — `app/components/Navbar.vue` (menu → `/settings`, add → `/add`).
- **IconButton** — `app/components/IconButton.vue` (round soft-fill button, teal press flash).
- **Settings drawer** — `app/pages/settings.vue` + `SettingsAccount.vue` / `SettingsAbout.vue`,
  with animated slide transitions between sub-sections.
- **Add drawer shell** — `app/pages/add.vue` (bottom drawer, routes back to `/` on close).
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
- **PostCard v1** — `app/components/PostCard.vue`: date + title only (no image / type cue
  yet), whole card links to the post; rows divided by `border-silver-200`.
- **Context-aware navbar** — both slots swap per page: home = menu + add, feed page =
  sidebar icon (→ home) + search (no-op for now), post page = back (→ its feed) + save
  (no-op for now). Navigation is hierarchical, not history-based. See
  `docs/superpowers/specs/2026-07-03-feed-post-navigation-design.md`.
- **Reader slide transitions** — home → feed → post slide like a navigation stack (deeper
  pushes in from the right, back pops out to the right). Direction is set on route meta by
  `app/middleware/page-slide.global.ts` (computed *before* render — a component watch is one
  navigation late), shared `.page-slide-*` classes live in `assets/css/main.css`, and the
  default layout provides the positioning/clip context. Non-reader routes (add, settings)
  swap instantly (`page-none`) so their drawer animations own the motion; the settings
  drawer's internal slides reuse the same CSS classes via `usePageSlide()`.

## Stubs (exist but placeholder content)

- `app/pages/add.vue` — drawer works; the form body is a placeholder header.

## Not started

- **Feed page (rest)** — the `usePostList(uid)` resolver (saved → folder → feed, per-feed
  filtering, folder mute). Includes `/feed/saved`.
- **Post page (rest)** — Save + Open source actions.
- **Master/detail layout** — single pane on mobile, two panes (feed list + post / settings nav
  + subpage) on desktop, off the same nested routes.
- **Settings rework** — split the demo drawer into nested routed subpages (`/settings/account`,
  `/settings/appearance`, `/settings/about`, `/settings/report`) with page-level transitions.
- **PostCard (rest)** — image and source-feed type cue.
- **Add feed form** — URL input + type detection + VeeValidate/Zod validation.
- **Saved posts** — a **Saved** feed pinned in the feeds list (no separate screen, no navbar
  icon) that lists all saved posts; plus the saved state itself.
- **Folders (rest)** — the `Folder` type, one mock folder, and the expandable rows on the
  home list are done (see Built). Still missing: the folder merged-stream read (`/feed/[uid]`
  with a folder uid, via the `usePostList(uid)` resolver), the navbar **+** create menu (New
  feed / New folder), a New-folder drawer, an edit context menu (long-press / 3-dot) for
  rename, add/remove feeds, per-folder mute, and delete, plus a folders store. See
  [data-model.md](./data-model.md#folder-new--not-yet-in-code) and
  [screens-and-flows.md](./screens-and-flows.md).
- **State layer** — Pinia store(s) for feeds, folders, posts, and saved state (Pinia installed,
  no stores yet).
- **Data fetching / RSS** — no `server/` routes, no `$fetch`/`useAsyncData`, no parser. All
  data is static. The fetching + persistence stack is undecided (to be specced separately).

## Installed but unused

- **Pinia** (`@pinia/nuxt`) — no stores yet.
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
