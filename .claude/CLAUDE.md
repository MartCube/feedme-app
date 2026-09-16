# FeedMe

Reeder-inspired, distraction-free news aggregator — minimal, functional, scalable;
minimalism is the product. Mobile-first UI, Capacitor planned. Runs on the real Django
API — the mock data files are gone and there is no fallback path, so the backend must be
up (`docker compose up -d`) for the app to render anything.

Nuxt 4 (Vue 3 + TypeScript), source in `app/`, pnpm. @nuxt/ui v4 bundles Tailwind v4,
@nuxt/icon, @nuxt/fonts, @nuxt/color-mode — don't install/configure those separately.

## Before you build

- `docs/` is the product spec — read it first; `docs/current-state.md` tracks what's built.
- Visual work: `docs/design-system.md` is the source of truth for tokens and treatments.
- `pending_tasks/` is the user's private backlog — ignore it unless explicitly pointed at a task.
- Before using a Nuxt UI component, VueUse composable, or library API not already used
  somewhere in this repo — or before adding any dependency — delegate to the `librarian`
  agent first. Library-first: prefer VueUse/Nuxt UI/Nuxt built-ins over new deps.
- When asked to commit after building work, delegate to the `checker` agent first
  (lint + typecheck; ruff + pytest + migrations check when `backend/` changed) — plus the
  `design-reviewer` agent when the work touched UI — then the `docs` agent to sync docs/
  with what was built, then hand off to the `git` agent.
- Frontend work in `app/`: use the `frontend-dev` skill (running it, the mobile/desktop
  shell). `new-component` is the narrower companion for scaffolding one component.
- Backend work in `backend/`: use the `backend-dev` skill (compose workflow, host venv).

## Conventions

- **The hard rules live in `.claude/rules/` and load themselves** when you read a matching
  file: `components.md` (any `.vue`, css), `shell.md` (layouts, desktop shell, pages,
  middleware), `data-layer.md` (stores, plugins, composables), `backend.md` (`backend/**/*.py`).
  Creating a new file? Read a sibling first so the rules are in context.
- 2-space indent, single quotes, no semicolons — a PostToolUse hook runs `eslint --fix` on
  every edited `.vue`/`.ts`/`.mjs`; a second runs `ruff check --fix` + `ruff format` on every
  edited `.py`. Don't hand-format.
- Hooks enforce the invariants deterministically (`.claude/hooks/`, tests in
  `test-guards.sh`): no `.env`, lockfile, `app/types/api.d.ts` or migration edits; no drawer
  route pages under `app/pages/{settings,add,edit}*`; no new markdown outside `docs/`,
  `.claude/`, `pending_tasks/`; no foreground `pnpm dev` / `docker compose up` (background
  them or use `-d`); pnpm only, never npm/npx/yarn.
- Vocabulary is shared end to end — `Feed`, `Folder`, `Post`, `Saved`; `Source` is
  backend-only. No wrapper composables around Pinia stores. Spacing is the default separator;
  hairline dividers are allowed, never stacked with gap + card edge. No gloss; elevation is
  `shadow-elevated`.
