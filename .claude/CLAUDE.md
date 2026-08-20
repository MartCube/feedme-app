# FeedMe

Reeder-inspired, distraction-free news aggregator — minimal, functional, scalable;
minimalism is the product. Mobile-first UI, Capacitor planned. Frontend-only phase:
runs on mock data (app/assets/data.ts); Django backend planned.

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
  (lint + typecheck) — plus the `design-reviewer` agent when the work touched UI — then the
  `docs` agent to sync docs/ with what was built, then hand off to the `git` agent.
- Backend work in `backend/`: use the `backend-dev` skill (compose workflow, django-ninja
  conventions, and the vocabulary the API shares with the frontend).

## Conventions

- 2-space indent, single quotes, no semicolons — a PostToolUse hook runs `eslint --fix` on
  every edited `.vue`/`.ts`/`.mjs`, so don't hand-format. Python is the same deal: a second hook
  runs `ruff check --fix` + `ruff format` on every edited `.py`, from the host `.venv`.
- No `<style>` blocks in components — utilities in the template; the rest in `app/assets/css/`.
- No wrapper composables around Pinia stores — use stores directly.
- Drawers (settings, add) mount in the **layout**, never as nested route pages — nested
  routes remount the host page (known Nuxt trap, details in .claude/memory gotchas).
  A PreToolUse hook blocks `app/pages/{settings,add,edit}*`, along with `.env` and the lockfile.
- Separation: spacing is the default, **hairline dividers are allowed** where spacing
  doesn't carry the grouping — but never stack divider + gap + card edge. No gloss;
  elevation is `shadow-elevated`. See `docs/design-system.md` § Separation.


