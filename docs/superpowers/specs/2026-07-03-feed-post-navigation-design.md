# Feed & Post pages — navigation-first v1

Date: 2026-07-03
Scope: home → feed → post reading flow. Main focus is **navigation**; the pages themselves
stay deliberately simple. Follows [screens-and-flows.md](../../screens-and-flows.md) §2–3
with temporary simplifications noted below.

## Goal

Make the three reading pages navigable end to end on mock data:

- **Home** (`/`) — exists. Tap a feed/folder row → feed page.
- **Feed** (`/feed/[uid]`) — list of PostCards. Tap a card → post page. Back → home.
- **Post** (`/feed/[uid]/post/[postUid]`) — full post. Back → the feed it was opened from.

The navbar (menu + add) is used on exactly these three pages.

## Decisions

### The navbar is context-aware (both slots swap per page)

Navigation is **hierarchical, not history-based** (per the docs' cross-screen rules):

| Page | Left | Right |
|---|---|---|
| Home | menu → `/settings` | **+** menu (New feed / New folder) |
| Feed | sidebar icon → `/` | search (no-op until post filtering exists) |
| Post | back → `/feed/[uid]` | save (no-op until saved state exists) |

Alternatives considered:
- *Back button below the navbar* — two stacked bars, wastes vertical space on mobile.
- *Back replaces the whole navbar* — loses the per-page action slot on the right.
- *Same + menu on all three pages* — rejected: add belongs to home; feed/post pages get
  reading actions instead.

### Post list lives in `feed/[uid]/index.vue`; `[uid].vue` is a passthrough

The route tree already matches the docs. For this mobile-first pass, `feed/[uid].vue` renders
only `<NuxtPage />`; the post list renders in `[uid]/index.vue` and the post in
`post/[postUid].vue` — exactly one pane per route, nothing to conditionally hide.

When the desktop master/detail layout lands, the list moves up into `[uid].vue` (master) and
renders beside the detail — an additive refactor; routes don't change.

### Temporary simplifications (this pass only)

- **Every `uid` shows all posts** from all three mock feeds, newest first. The
  `usePostList(uid)` resolver (saved → folder → feed) comes when the data layer lands. The
  page title does resolve the folder/feed name from mock data so navigation feels real.
- **PostCard shows only date + title**, separated by the standard list divider
  (`border-b border-silver-200`, same as the home list). Image and type cue come later.
- **Post page shows only title, date, content.** The navbar's save button is a no-op;
  saved state and Open-source come later. The feed page's search button is likewise a no-op
  until post filtering exists.

## Components & files

| File | Change |
|---|---|
| `app/components/Navbar.vue` | Context-aware slots per the table above |
| `app/components/PostCard.vue` | `{ post, to }` props; whole card is a `NuxtLink`; date (small, muted) over title |
| `app/pages/feed/[uid].vue` | `<NuxtPage />` passthrough |
| `app/pages/feed/[uid]/index.vue` | Resolved title + `<ul>` of PostCards, all posts newest-first |
| `app/pages/feed/[uid]/post/[postUid].vue` | Title, date, content; "Post not found" fallback |
| `app/utils/format-date.ts` | `formatDate(iso)` → "22 Jun 2026" (auto-imported) |

## Testing

No test runner is set up in the project. Verification: `pnpm lint` plus exercising the flow in
the dev server (home → feed → post → back → back).
