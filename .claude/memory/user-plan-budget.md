---
name: user-plan-budget
description: User is on Claude Pro ($20) and wants maximum daily Claude use on FeedMe — rate every automation/agent idea by runtime token cost; deterministic hooks first, cheap subagent tiers, nothing always-on
metadata:
  type: user
---

The user runs Claude Code on the **$20 Pro plan** and wants to get the most out of it every day
on FeedMe. Token cost per session/turn is a first-class criterion for any tooling proposal.

**How to apply:**
- Prefer deterministic shell hooks (zero tokens) over `type: prompt`/`type: agent` hooks or
  extra subagents.
- Context should load only when relevant (path-scoped `.claude/rules/`, skills on invocation),
  never always-on.
- Subagent models follow [[feedback-model-policy]] — mechanical → haiku, judgment → sonnet, main
  loop opus. Never propose an opus subagent for a railed task.
- Don't propose installing config-collection plugins (e.g. everything-claude-code) wholesale —
  reviewed 2026-09-16, ~8 ideas adopted, the rest skipped as token-costly or duplicative.
