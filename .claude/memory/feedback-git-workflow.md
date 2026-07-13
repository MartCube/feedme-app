---
name: feedback-git-workflow
description: "Solo single-branch git flow — commit straight to main, no auto-branching, minimal ceremony"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d5967e06-e7a4-48b5-8c9e-4b8a63ae654d
---

Solo developer, no production branch yet. Keep git ceremony minimal: commit directly to
the current branch (`main`) by default; do NOT auto-create topic branches. Only branch
when explicitly asked. Still only push when asked, and never force-push / hard-reset /
rewrite history without an explicit request. Delegate git work (commit/push requests)
to the `git` subagent proactively — no need for the user to name the agent.

**Why:** One developer, no shared/production branch — topic-branch overhead buys nothing
here and just adds friction.

**How to apply:** Overrides the generic "if on the default branch, branch first" default.
Encoded in the `git` subagent ([[project-claude-dir-layout]]). Revisit if a backend or
production branch is introduced.
