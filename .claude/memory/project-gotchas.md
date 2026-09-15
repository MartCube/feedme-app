---
name: project-gotchas
description: "Traps learned the hard way in FeedMe (pnpm, Nuxt, Nuxt UI) — check here before \"fixing\" or simplifying related code"
metadata: 
  node_type: memory
  type: project
  originSessionId: c763d233-28e4-471e-ba38-8eb696e2ebc4
  modified: 2026-08-04T19:33:19.722Z
---

**pnpm / tooling:**
- **Do NOT upgrade to TypeScript 7 yet** (tried 2026-07-17, latest was 7.0.2). `vue-tsc` (latest
  3.3.7, Volar-based) still `require.resolve`s `typescript/lib/tsc`, which TS 7 removed from its
  `exports` → `nuxt typecheck` dies with `ERR_PACKAGE_PATH_NOT_EXPORTED`. The app *runs* on TS 7
  (Vite transpiles, doesn't typecheck) but you lose the only verification harness. Stay on TS 6
  until vue-tsc/Volar ships a TS-7-compatible release (watch its dist-tags for a `next`).
- `typescript` must stay a **direct devDependency**. pnpm doesn't hoist it from Nuxt's deps, and
  `@nuxt/eslint-config` silently disables TS parsing without it — every TS file then fails lint
  with "Parsing error: Unexpected token". Same reason `tailwindcss` is pinned directly, and
  `vue-tsc` too — without it `nuxt typecheck` spawns `npx` (not on PATH here) and dies with ENOENT.
- pnpm 11 fails **any** script (even `pnpm lint`) if a dep has an unapproved build script. Fix:
  in `pnpm-workspace.yaml` `allowBuilds`, flip the auto-added placeholder to `true`/`false`,
  re-run `pnpm install`.
- Node here is pnpm-managed (`pnpm env`) → **no npm/npx by default**; anything spawning `npx`
  (plugin MCP servers like context7, `nuxt typecheck` without direct `vue-tsc`) dies with
  ENOENT / "Failed to connect". Fixed once via `pnpm add -g npm`; if an MCP server won't
  connect, check `which npx` before debugging the server.

**Claude Code / plugins:**
- Plugin-bundled MCP tools are named `mcp__plugin_<plugin>_<server>__<tool>`
  (e.g. `mcp__plugin_context7_context7__get-library-docs`), not bare `mcp__<server>__…`.
  A wrong name in an agent's `tools:` fails **silently** — the agent just lacks the tool.
- Agent types (.claude/agents) and MCP tool registration load at **session start** — a new
  agent file or newly connected server needs a restart before it's usable/spawnable.

**Nuxt routing / transitions:**
- `pageTransition` in `definePageMeta` leaks into the ROOT NuxtPage's `route.meta` and **remounts
  the whole page tree**. For a nested NuxtPage, use the `:transition` prop, not meta.
- **Never use nested route pages for the settings drawer**: the host page
  remounts on first child navigation (Vue Suspense/NuxtPage internals, never fully pinned;
  nuxt#13094). That's why settings is one route `/settings/:panel?` reusing the home page file with
  `key: 'home'`, and `SettingsDrawer` lives in the **layout**, not a page.
- Navbar content must stay **fixed per page instance** (params captured once in setup, no
  route-driven computeds) — the route changes before the leave-slide finishes, so live values swap
  content on the leaving page mid-animation.
- A page whose root component teleports (UDrawer) needs a real element root or navigation breaks.

- **Nuxt's `useRoute()` only re-syncs when a `<NuxtPage>` resolves.** The desktop shell renders
  no NuxtPage, so `useRoute()` there is frozen forever after the first navigation — the URL
  changes but nothing updates. Any component that can render outside NuxtPage (desktop shell,
  sidebar, content overlay, shared settings/edit panels) must read
  `useRouter().currentRoute` instead. Mobile drawer HOSTS may keep `useRoute()` — the mobile
  tree always renders NuxtPage. (Also triggers a benign dev warning: "pages but `<NuxtPage/>`
  has not been detected".)
- **VueUse `useMediaQuery` reads matchMedia during the hydration render** — a bare
  `v-if="isDesktop"` layout branch hydration-mismatches on wide screens and leaves the DOM
  stuck with the server's mobile classes (invisible desktop shell, no error). The
  `useMounted()` gate inside `useIsDesktop()` (app/composables/useIsDesktop.ts) is
  load-bearing; don't "simplify" it away.

**Scrollbars (custom `::-webkit-scrollbar`):**
- Chromium **ignores `:hover` on the scrolling element** when resolving scrollbar
  pseudo-elements — `.pane:hover::-webkit-scrollbar-thumb` never applies, so a CSS-only
  hover-reveal scrollbar is not buildable. `::-webkit-scrollbar-thumb:hover` (the thumb's
  own hover) DOES work, and a class/attribute toggled on an ancestor DOES re-resolve them,
  so JS is the only route to a reveal-on-hover.
- Chromium 121+ **drops all `::-webkit-scrollbar` rules** on an element that also sets
  `scrollbar-width`/`scrollbar-color`. Split the two APIs with
  `@supports selector(::-webkit-scrollbar)` / `@supports not …`; never let them meet.

**Verifying scrollbars headlessly (puppeteer):**
- Puppeteer launches with `--hide-scrollbars` by default → layout still reserves the gutter,
  but nothing paints. Pass `ignoreDefaultArgs: ['--hide-scrollbars']`.
- `page.screenshot({ clip })` defaults to `captureBeyondViewport: true`, which re-renders
  without scrollbars. Set `captureBeyondViewport: false`.
- Headless reports `pointer: coarse`, so any `@media (pointer: fine)` rule is dead. Force it
  with `--blink-settings=primaryPointerType=4,availablePointerTypes=4` — but note
  `page.setViewport()` **wipes that override**, so re-measure only after a reload, never
  after a resize, or you'll chase a phantom regression.

**Nuxt UI / vaul:**
- Theme **compound variants** apply after `app.config.ts` slot classes and win in tailwind-merge —
  override via a matching `compoundVariants` entry in app.config, not slot classes.
- tailwind-merge must be TAUGHT the custom @theme tokens or `:ui` overrides like `px-sm` won't
  replace component defaults like `px-3` (both land in the DOM, CSS order decides; unknown
  `text-*` names even get misread as text-COLOR and strip the real color class). Fixed via
  `app.config.ts` → `ui.tv.twMergeConfig.extend.theme` (`spacing` + `text` keys) — Nuxt UI passes
  `ui.tv` straight to tailwind-variants' `createTV`. A NEW spacing/type token must be added there
  too, or it silently regresses. Verify by reading the rendered `className` — the loser class is
  still present when merging failed.
- vaul emits `animationEnd(false)` once for its initial *closed* state after mount.
- vaul's `should-scale-background` mutates `<body>` inline styles — see
  [[feedback-no-global-visual-side-effects]].

## Backend editing

- The PostToolUse hook runs `ruff check --fix` on every Edit/Write of a `.py` — and F401
  deletes an import the moment it is unused. Adding an import in one edit and its first use in
  a later edit loses the import in between (`NameError` at test time). Put the import and its
  use in the same edit, or add the use first and the import second.
- `worker` and `scheduler` don't autoreload — `api` (runserver) does. After editing anything
  they import (`core/ingest.py`, `core/retention.py`, `core/tasks.py`), `docker compose restart
  worker scheduler` or they keep running the old code.
- Probing the real API from `manage.py shell`: `django.test.Client` needs
  `headers={'host': 'localhost'}` (pytest patches ALLOWED_HOSTS; the shell doesn't), and
  wrap in `transaction.atomic()` + `set_rollback(True)` — with a nested `atomic()` per probe,
  or the first DataError poisons every probe after it.
