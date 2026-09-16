---
name: commit
description: Run FeedMe's pre-commit chain and commit — checker (+ design-reviewer when UI changed) → docs sync → git. Halts on checker problems.
disable-model-invocation: true
---

# /commit — the pre-commit chain, in order

`$ARGUMENTS` is the intent for the commit message (optional). The chain is the one in
CLAUDE.md; this skill exists so no step is forgotten and no agent is spawned that the change
doesn't need.

## 1. Scope

```bash
git status --porcelain
```

Nothing to commit → say so and stop. Otherwise note which sides changed: `app/` (frontend),
`backend/` (backend), `.vue`/`.css` (UI), `docs/` or `.claude/` only (config/docs).

## 2. Verify — spawn in parallel, one message

- **`checker`** always, with the scope from step 1. It runs lint + typecheck for frontend
  changes and ruff + pytest + `makemigrations --check` for backend changes.
- **`design-reviewer`** only if a `.vue` or `.css` file changed.

**Checker reports problems → hard stop.** Report them, fix them (or hand them to the user if
they're outside the change), then run `/commit` again. Do not commit over a red check.

**Design-reviewer reports findings →** fix the mechanical ones (an off-scale token, a stray
`<style>`, a stacked divider) and re-run it; surface judgment calls to the user and stop —
they decide whether it ships as-is.

## 3. Docs

Spawn **`docs`** unless the change touched only `.claude/`. It syncs `docs/current-state.md`,
the roadmap § Status and any affected spec doc from the diff, and reports "docs/ in sync" or
"conflicts need your call". A conflict → stop and surface it.

## 4. Commit

Spawn **`git`** with the intent from `$ARGUMENTS` (or a one-line summary of the diff if none),
the list of related paths to stage, and the reminder that it commits to the current branch
and does not push unless asked. Relay its summary: files staged, subject, branch.
