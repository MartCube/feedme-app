# Claude Code — practical guide for this project

## Starting a fresh project

1. **Create `CLAUDE.md` first.** Put it in the project root. This file is read automatically at the
   start of every session. Include: what the project does, the tech stack, key commands, and any
   non-obvious constraints. Keep it short — it's loaded every time.

2. **Tell Claude your stack before writing any code.** "We're using Nuxt 4, pnpm, TypeScript strict,
   no semicolons" saves you from correcting style issues later.

3. **Set up tooling early.** ESLint, TypeScript, formatter — ask Claude to set these up in session 1
   so every file written afterwards is already compliant.

---

## The `.claude/` folder — everything Claude-related lives here

- `memory/` — Claude's persistent memory (canonical location). The harness directory
  `~/.claude/projects/-home-martcube-projects-feedme/memory` is a **symlink** to this folder, so
  there is exactly one copy. Gitignored.
- `superpowers/plans/` — implementation plans written by superpowers skills
- `superpowers/specs/` — design/spec docs from brainstorming sessions
- `superpowers/scratch/` — transient run files (task briefs, reports, diffs); deleted after a run
  ships. Gitignored.
- `settings.local.json` — permissions (broad allow inside the project + the memory dir; deny list
  for deletions and dangerous commands)

Nothing superpowers- or Claude-related goes in `docs/` (product spec only) or the repo root.

### Memory

- `MEMORY.md` — the index (keep it short)
- one file per fact, named `feedback-*` / `project-*`

**Edit them freely.** If Claude does something wrong, correct it in chat ("don't use double quotes
here") and it will update the memory file so the same mistake doesn't happen again.

### Model policy

Fable for everything by default, including subagents (passed explicitly on every dispatch). Opus is
the fallback when Fable runs out. Sonnet only for narrow mechanical subtasks to save tokens —
Claude says so when it does. Never Haiku for code.

---

## How to get the best results

### Be specific and reference file paths
Bad: "fix the login"
Good: "In `app/pages/login.vue:42`, the submit handler is calling `navigateTo` before `await
signIn()` resolves. Fix the ordering."

### One concern per message
Each message should have one clear goal. Don't bundle "refactor this + add tests + also update
the README" — split them.

### Show context, not just symptoms
"ESLint is failing" is hard to help with. "Running `pnpm lint` gives this error: [paste error]" is
actionable immediately.

### Ask for a plan first on large tasks
For anything that touches more than 3 files, ask: "What's your plan for this?" before Claude
starts writing. You can redirect before any code is written.

### Use `!` to run commands yourself
If Claude asks you to run something interactively (like `gcloud auth login`), type `! <command>`
in the prompt. The output flows back into the conversation.

---

## Nuxt 4 patterns for this project

### Adding a new page
Pages live in `app/pages/`. File name = route. `app/pages/index.vue` → `/`.

### Adding a composable
Put it in `app/composables/`. Nuxt auto-imports anything there — no need to import manually.

### Adding a module
1. `pnpm add -D <module-name>`
2. Add to `modules` array in `nuxt.config.ts` (keep `modules` as the first key)
3. Run `pnpm nuxi prepare` to regenerate types

### Key commands
```bash
pnpm dev          # start dev server (http://localhost:3000)
pnpm lint         # check for ESLint errors
pnpm lint:fix     # auto-fix ESLint errors
pnpm build        # production build
pnpm nuxi prepare # regenerate .nuxt types (needed after config changes)
```

---

## What Claude won't do without asking

- Push to git / create PRs
- Delete files or branches
- Install packages (will ask first on large additions)
- Modify CI/CD pipelines

If you want more autonomy ("just fix it, don't ask"), say so explicitly in your message.
