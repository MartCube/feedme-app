# Memory Index

- [Gotchas](project-gotchas.md) — traps learned the hard way: pnpm typescript/vue-tsc/allowBuilds/no-npx, plugin MCP tool naming + session-start loading, Nuxt remount quirks, Nuxt UI/vaul; check before "fixing" related code
- [Claude dir layout](project-claude-dir-layout.md) — everything Claude-Code/superpowers-related lives under .claude/ (plans, specs, scratch, memory); never in docs/ or root
- [Docs are source of truth](project-docs-source-of-truth.md) — docs/ is the agreed product spec, check it before building; current-state.md tracks status/decisions; batch doc edits at session end / pre-commit
- [Naming taste](feedback-naming-taste.md) — no enterprise-speak entity names (Subscription vetoed → Feed); backend + frontend share the same nouns; check docs/backend.md vocabulary table
- [Model policy](feedback-model-policy.md) — Fable default for everything incl. subagents, Opus fallback, Sonnet only for trivial mechanical subtasks, never Haiku for code
- [Full access, direct execution](feedback-full-file-access.md) — blanket read/edit on all project files, no permission asking; no subagent/task ceremony for simple fixes
- [Discuss before building](feedback-discuss-before-building.md) — for ANY building work: present plan/strategy, discuss, agree, then act; simple concrete fixes exempt
- [Memory style](feedback-memory-style.md) — rules + how-to-avoid only, no incident details; repo facts belong in CLAUDE.md, not memory; nothing derivable from repo files
- [Visual taste](feedback-visual-taste.md) — no divider lines in lists, no glossy rings; spacing + soft shadows (see docs/design-system.md)
- [Design tokens in CSS](feedback-design-tokens-in-css.md) — scales (spacing/type) belong as real @theme tokens in a dedicated app/assets/css file (like typography.css), not doc-only conventions
- [No global visual side effects](feedback-no-global-visual-side-effects.md) — never mutate body/layout backgrounds from component work
- [Verification approach](feedback-verification-approach.md) — no test harness; verify via pnpm lint + typecheck + run app, user manually reviews; add Vitest for store logic later
- [Git workflow](feedback-git-workflow.md) — solo single-branch; commit straight to main, no auto-branching, only push when asked; delegate commits/pushes to the git subagent proactively
