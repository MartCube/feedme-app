---
name: feedback-model-policy
description: "Model policy: Fable for everything by default (incl. subagents), Opus as fallback, Sonnet only for trivial mechanical subtasks, never Haiku for code"
metadata:
  type: feedback
---

Use the best models available. Fable is the default for all work including subagent dispatches;
Opus is the fallback when Fable capacity/tokens run out. Sonnet is allowed only for narrow,
mechanical subtasks (mass renames, boilerplate, repetitive edits). Never Haiku for code work.

**Why:** quality first — skills/workflows quietly dispatching smaller models produce worse results;
token savings only where the task genuinely can't benefit from a stronger model.

**How to apply:** when dispatching any subagent, pass `model` explicitly (default `fable`) — never
rely on a skill's or agent definition's default. If choosing Sonnet for a subtask, say so and why.
Relates to [[feedback-full-file-access]] (often the right move is no subagent at all).
