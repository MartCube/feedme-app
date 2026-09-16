---
name: frontend-dev
description: Work on the FeedMe Nuxt frontend — running it, the mobile/desktop shell architecture, and where the hard rules live
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

**The hard rules load themselves.** `.claude/rules/` is path-scoped: `components.md` (any
`.vue`, `app/assets/css/`), `shell.md` (layouts, desktop shell, pages, middleware,
`nuxt.config.ts`), `data-layer.md` (stores, plugins, composables, `app.vue`). They enter
context when you *read* a matching file — so when creating a new file, read a sibling in the
target folder first.

Adjacent, don't duplicate: **`new-component`** scaffolds a component that speaks the design
system, **`verify`** drives the running app headlessly, the **`design-reviewer`** agent
judges design drift, **`checker`** runs lint + typecheck, **`librarian`** answers
third-party API questions.

## Running it

```bash
pnpm dev                    # :3000 — run it backgrounded; the Bash guard blocks it foreground
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
with the `verify` skill and looking at pixels. The PostToolUse `eslint --fix` hook fires on the
Write/Edit tools only — a file written from the shell needs `pnpm exec eslint --fix <file>`.

## The shell — this is the part that surprises people

`app/layouts/default.vue` is the only layout and the single mobile/desktop branch point,
on `useIsDesktop()` (VueUse `useMediaQuery` at `lg`/1024px, gated behind `useMounted` so
SSR and hydration always render the mobile tree). `isDesktopNow()` is the synchronous twin
for imperative guards that run before the reactive ref flips.

Mobile is the single-pane stack: pages slide left/right, and settings / add / edit are vaul
bottom sheets mounted in the layout. Desktop is sidebar | posts | post, with settings / add
/ edit rendered as a master–detail pair over the reading panes, which stay mounted so
closing restores the reading position and scroll exactly. **On desktop no route renders a
`<NuxtPage>`** — `DesktopShell` composes its columns from the router and the stores; the
consequences (frozen `useRoute()`, transition traps, drawer hosting) are in `rules/shell.md`.

Headless Chrome reports `(hover: none)`, so hover-gated affordances render in their touch
form under the `verify` skill. Emulate or inject to see the desktop branch.

## Vocabulary

The UI, the API and the database share **the same nouns** — `Feed`, `Folder`, `Post`,
`Saved`; `Source` is backend-only and must never appear on screen. Uid prefixes and the
resolver order are in `rules/data-layer.md`; the full table is `docs/backend.md`
§ Vocabulary. A new public noun is a discussion, not a unilateral call.

## Before committing

`design-reviewer` (if UI changed) and `checker`, then `docs` to sync `docs/`, then hand off
to `git`.
