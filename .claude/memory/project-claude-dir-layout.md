---
name: project-claude-dir-layout
description: "Everything Claude-Code-related (superpowers plans/specs/scratch, settings, memory) lives under .claude/ — never in docs/ or project root"
metadata:
  type: project
---

All Claude Code / plugin artifacts live under `.claude/`:

- `.claude/memory/` — persistent memory (canonical location; the harness dir
  `~/.claude/projects/-home-martcube-projects-feedme/memory` is a symlink to it; gitignored)
- `.claude/superpowers/plans/` — implementation plans written by superpowers skills
- `.claude/superpowers/specs/` — design/spec docs from brainstorming sessions
- `.claude/superpowers/scratch/` — transient run files; delete after the run ships
- `.claude/settings.local.json` — permissions config

`docs/` is reserved for the product spec ([[project-docs-source-of-truth]]) and `pending_tasks/`
for the user's private backlog (contract in `CLAUDE.md`: ignore unless explicitly pointed at a task).

**How to apply:** when any skill wants to write plans, specs, or scratch files, redirect the output
to the matching `.claude/superpowers/` subfolder regardless of the skill's default. Never create
such folders in docs/ or the repo root.
