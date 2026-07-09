---
name: project-docs-source-of-truth
description: "docs/ is FeedMe's agreed product spec — check it before building; current-state.md tracks progress and open decisions; batch doc edits at session end"
metadata:
  type: project
---

The `docs/` folder is FeedMe's **product source of truth**: overview, user stories, screens/flows,
data model, design system, and `current-state.md` (implementation status + open decisions).
The user wrote it both for their own clarity and as a north star for AI.

**How to apply:**
- Before building a feature, check `docs/` first — spec beats assumptions.
- For what's done/pending/undecided, read `docs/current-state.md`; never copy its open decisions
  into memory (they rot on decision day).
- **No `docs/` edits mid-session**: batch doc updates at session end or right
  before a git commit, updating `current-state.md` as work lands.

Related: [[feedback-discuss-before-building]].
