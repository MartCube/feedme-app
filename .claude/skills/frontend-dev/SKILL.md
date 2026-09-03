---
name: frontend-dev
description: Work on the FeedMe Nuxt frontend — running it, the mobile/desktop shell architecture, the routing traps that bite, and the vocabulary the UI shares with the API
---

# FeedMe frontend

Nuxt 4 (Vue 3 + TypeScript) in `app/`, pnpm. `@nuxt/ui` v4 bundles Tailwind v4, `@nuxt/icon`,
`@nuxt/fonts` and `@nuxt/color-mode` — never install or configure those separately.
`docs/` is the product spec; read the relevant screen in
[screens-and-flows.md](../../../docs/screens-and-flows.md) before building, and
[design-system.md](../../../docs/design-system.md) before styling. This skill is the
working shorthand for everything *around* the pixels.

**Status check first.** `docs/current-state.md` says what actually exists — it is kept
current and it is the fastest way to avoid rebuilding something. Read the code before
assuming a store field, route, or component is there.

Adjacent, don't duplicate: **`new-component`** scaffolds a component that speaks the design
system, **`verify`** drives the running app headlessly, the **`design-reviewer`** agent
judges design drift, **`checker`** runs lint + typecheck, **`librarian`** answers
third-party API questions.

## Running it

```bash
pnpm dev                    # :3000
pnpm dev:mobile             # --public --qr, for a real phone on the LAN
pnpm lint                   # eslint .
pnpm typecheck              # nuxt typecheck (vue-tsc)
pnpm types:api              # regenerate app/types/api.d.ts from the live OpenAPI schema
```

**The backend must be up** or every screen renders its unreachable state:
`docker compose up -d` (see the `backend-dev` skill). The API base defaults to
`http://localhost:8000/api/v1`; override with `NUXT_PUBLIC_API_BASE`.

Signing in needs a token — `docker compose exec api python manage.py issue_token <email>`
mints one for the dev-token field on `/login`.

There is no test harness. Verification is `pnpm lint` + `pnpm typecheck` + driving the app
with the `verify` skill and looking at pixels.

## The data layer

- **`$api` is the only way to reach the server** (`app/plugins/api.ts`) — a single
  `$fetch.create` that attaches the bearer and, on 401, clears the session and routes to
  `/login`. Never call bare `$fetch` against the API.
- **Types are generated, never written.** `pnpm types:api` writes `app/types/api.d.ts`
  (committed, ESLint-ignored); `app/assets/types.ts` is a thin alias layer over
  `components['schemas']`. Hand-editing either one puts the frontend out of sync with the
  contract instead of revealing that it already is.
- **Every call is client-only.** SSR renders the shell; account data loads in `app.vue`'s
  `onMounted`, never in middleware. Each store captures `useNuxtApp()` at setup, because
  actions resume past `await` boundaries where `useNuxtApp()` has no context to find.
- Stores are `auth`, `feeds`, `settings`. Writes are optimistic-with-rollback except
  `addFeed`/`addFolder`, which await server-minted uids. **No wrapper composables around
  stores** — use them directly.

## The shell — this is the part that surprises people

`app/layouts/default.vue` is the only layout and the single mobile/desktop branch point,
on `useIsDesktop()` (VueUse `useMediaQuery` at `lg`/1024px, gated behind `useMounted` so
SSR and hydration always render the mobile tree). `isDesktopNow()` is the synchronous twin
for imperative guards that run before the reactive ref flips.

> **On desktop no route renders a `<NuxtPage>` at all.** `DesktopShell` composes its three
> columns from the router and the stores. So inside the shell, the sidebar, the content
> area and the panels they host, **`useRoute()` never updates** — Nuxt only re-syncs its
> route object when a `<NuxtPage>` resolves. Use `useRouter().currentRoute`.

Mobile is the single-pane stack: pages slide left/right, and settings / add / edit are vaul
bottom sheets mounted in the layout. Desktop is sidebar | posts | post, with settings / add
/ edit rendered as a master–detail pair over the reading panes, which stay mounted so
closing restores the reading position and scroll exactly.

## Traps

- **Drawers mount in the layout, never as pages.** `app/pages/{settings,add,edit}*` is
  blocked by a PreToolUse hook. Their URLs are synthesized in `nuxt.config.ts`'s
  `pages:extend` against the home page component with a shared `meta: { key: 'home' }`, so
  the feed list stays mounted behind them. Nested route pages remount their parent page on
  child navigation (nuxt#13094) — this was tried twice and reverted twice.
- **`pageTransition` in `definePageMeta` leaks into the root `<NuxtPage>`'s route meta and
  remounts the whole page tree.** Route transitions are set from
  `middleware/page-slide.global.ts`; for a nested `<NuxtPage>` use the `:transition` prop.
- **Panel slide direction rides CSS variables under a *fixed* transition name**
  (`utils/panel-slide.ts` + `.panel-slide-*` in `assets/css/transitions.css`). Switching the
  transition *name* does not work: Vue binds leave hooks to the name a panel **entered**
  under, so the leaving panel animates with a stale direction or not at all.
  `--panel-duration: 0s` is the no-direction default, and it is load-bearing — a leaving
  panel is `position: absolute` over the entering one, so a non-zero duration with no
  movement freezes stale content on screen.
- **Equal depth is sideways, not deeper.** `panelSlideDirection` returns `none` for it. A
  `<` comparison alone silently animates a sibling move as a push.
- **`isDesktopNow()` guards in the drawer hosts** stop a bottom sheet flashing during a
  desktop deep-load, before the reactive breakpoint flips. Don't remove them.
- Headless Chrome reports `(hover: none)`, so hover-gated affordances render in their touch
  form under the `verify` skill. Emulate or inject to see the desktop branch.

## Vocabulary

The UI, the API and the database share **the same nouns** — drift here is the expensive
mistake, and enterprise-speak is vetoed (`Subscription` was rejected in favour of `Feed`).
`Feed`, `Folder`, `Post`, `Saved`. **`Source` is backend-only and must never appear on
screen**: what the reader sees is *their* feed, not the global endpoint behind it.

Uids are prefixed and the backend mints them: `feed_*`, `folder_*`, `post_*`, the fixed
`saved_*` groups (`app/utils/saved.ts`), plus the literals `all` and `saved`. The feed
resolver reads them in that order, which is what lets one polymorphic `/feeds/{uid}/posts`
serve a feed, a folder, `all` and `saved` alike. A new public noun is a discussion, not a
unilateral call — check `docs/backend.md` § Vocabulary and the `backend-dev` skill.

## Ground rules

- **No `<style>` block, ever.** Utilities in the template; anything that can't be a utility
  becomes a token or `@utility` in `app/assets/css/`.
- 9 color roles, 4 text sizes, 6 spacing steps. No raw hex, no `text-sm`/`p-4`, no one-off
  `rgba()`. Outside the scales is a design discussion — stop and ask.
- **Justify every new composable or util, or cut it.** In a plan, say plainly which part is
  *moved* code and which is *new*.
- **Ask the `librarian` agent** before writing against a Nuxt UI / VueUse / Pinia / Tailwind
  API not already used in this repo, and before adding any dependency. Library-first:
  prefer what the stack already ships.
- Never mutate `body` or layout backgrounds from a component.
- 2-space indent, single quotes, no semicolons. A PostToolUse hook runs `eslint --fix` on
  every edited `.vue`/`.ts`/`.mjs` — but it fires on the Write/Edit tools only, so if you
  write a file from the shell, run `pnpm exec eslint --fix <file>` yourself.
- Before committing: `design-reviewer` (if UI changed) and `checker`, then `docs` to sync
  `docs/`, then hand off to `git`.
