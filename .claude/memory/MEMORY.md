# Memory Index

- [Gotchas](project-gotchas.md) — traps learned the hard way: pnpm typescript/vue-tsc/allowBuilds/no-npx, plugin MCP tool naming + session-start loading, Nuxt remount quirks, Nuxt UI/vaul, custom scrollbars + verifying them headlessly; check before "fixing" related code
- [Claude dir layout](project-claude-dir-layout.md) — everything Claude-Code/superpowers-related lives under .claude/ (plans, specs, scratch, memory); never in docs/ or root
- [Docs are source of truth](project-docs-source-of-truth.md) — docs/ is the agreed product spec, check it before building; current-state.md tracks status/decisions; batch doc edits at session end / pre-commit
- [Naming taste](feedback-naming-taste.md) — no enterprise-speak entity names (Subscription vetoed → Feed); backend + frontend share the same nouns; check docs/backend.md vocabulary table
- [Model policy](feedback-model-policy.md) — k3 default; k2.7-code for code-search subagents, k2.6 only for mechanical ones (git, checker); IDs at platform.kimi.ai/docs/models
- [Full access, direct execution](feedback-full-file-access.md) — blanket read/edit on all project files, no permission asking; no subagent/task ceremony for simple fixes
- [Discuss before building](feedback-discuss-before-building.md) — for ANY building work: present plan/strategy, discuss, agree, then act; simple concrete fixes exempt
- [Ask, don't assume](feedback-ask-dont-assume.md) — confirm uncertain facts (browser, symptoms, what was tried) with the user before building diagnostic steps or plans on them
- [Memory style](feedback-memory-style.md) — rules + how-to-avoid only, no incident details; repo facts belong in CLAUDE.md, not memory; nothing derivable from repo files
- [Visual taste](feedback-visual-taste.md) — spacing is the default separator, dividers allowed but never stacked with other signals; no glossy rings (see docs/design-system.md)
- [Design tokens in CSS](feedback-design-tokens-in-css.md) — scales (spacing/type) belong as real @theme tokens in a dedicated app/assets/css file (like typography.css), not doc-only conventions
- [No global visual side effects](feedback-no-global-visual-side-effects.md) — never mutate body/layout backgrounds from component work
- [Verification approach](feedback-verification-approach.md) — no test harness; verify via pnpm lint + typecheck + run app, user manually reviews; add Vitest for store logic later
- [Git workflow](feedback-git-workflow.md) — solo single-branch; commit straight to main, no auto-branching, only push when asked; delegate commits/pushes to the git subagent proactively
- [Mock data realism](project-mock-data-realism.md) — all uids show ALL mock posts on purpose; usePostList resolver deferred until real data
- [Minimal machinery](feedback-minimal-machinery.md) — justify every new composable/util in detail or cut it; separate "moved code" from "new code" in plans
