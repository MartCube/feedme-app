---
name: feedback-model-policy
description: "Model policy (Claude Pro era, since 2026-09-16): main loop opus; judgment/prose subagents sonnet; tightly-railed mechanical subagents haiku — tier by failure cost, never opus for a railed task"
metadata:
  type: feedback
---

Main loop runs Opus (judgment lives there). Subagents pin their own `model:` in
`.claude/agents/*.md`, tiered by the task's failure cost:

| Tier | Alias | Agents |
|---|---|---|
| judgment / prose | `sonnet` | docs, librarian, design-reviewer, explorer |
| mechanical, railed | `haiku` | checker, git |

The earlier Kimi-era pins (`kimi-k3` / `kimi-k2.7-code` / `kimi-k2.6`) were remapped on
2026-09-16 — no router was present, so they couldn't resolve in Claude Code.

**Why:** quality first, but on the Pro plan ([[user-plan-budget]]) an opus subagent for a task
that can't benefit from it is the single most expensive habit. A wrong answer from too weak a
model still costs more than the tokens saved — so `haiku` only where the task is fully railed.

**How to apply:** don't override an agent's pinned model with a weaker one at dispatch. When
creating a new subagent, pick the tier by failure cost and say why. Bump `docs` to opus by hand
only when drafting a whole new spec doc. Relates to [[feedback-full-file-access]].
