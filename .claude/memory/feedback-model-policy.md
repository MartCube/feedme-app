---
name: feedback-model-policy
description: "Model policy (Kimi era): k3 default; k2.7-code for code-search subagents, k2.6 only for tightly-railed mechanical subagents"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 96ccb424-2068-4d4b-9f7d-37a50b517cb1
  modified: 2026-07-24T17:06:43.035Z
---

Main loop and judgment/accuracy-critical subagents run `kimi-k3`; code-search subagents run
`kimi-k2.7-code`; tightly-railed mechanical subagents (git ops, lint/typecheck running) run
`kimi-k2.6`. Model IDs verified at platform.kimi.ai/docs/models.

**Why:** quality first — a wrong answer from a weaker model costs more than the tokens it
saves. Smaller models only where the task genuinely can't benefit from a stronger one.

**How to apply:** each `.claude/agents/*.md` pins its own `model:` — don't override it with
a weaker one at dispatch. When creating a new subagent, pick the tier by the task's failure
cost and say why. Relates to [[feedback-full-file-access]].
