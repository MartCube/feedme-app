---
name: feedback-no-browser-in-plan-mode
description: "Don't drive the chrome-devtools browser while planning — each action can prompt the user despite the allow rule; gather evidence with Bash and put browser checks after approval"
metadata:
  node_type: memory
  type: feedback
  originSessionId: ff5faa63-d4dd-4869-bbf1-bba2bcac845b
  modified: 2026-09-24T21:42:57.906Z
---

Don't call chrome-devtools MCP tools (new_page, emulate, evaluate_script, …) while plan mode is
active. Gather planning evidence with Bash instead — curl, `docker compose logs`, `manage.py
shell` — and put browser checks in the plan's verification step, to run after approval.

**Why:** in plan mode every browser action raised a permission prompt even though
`.claude/settings.local.json` allows the whole server (`mcp__chrome-devtools`), and "don't ask
again" didn't stop them. The user finds a stream of prompts maddening — it reads as a loop.

**How to apply:** before any browser work, confirm the allow list holds `mcp__chrome-devtools`
(the whole-server rule — never collect per-tool entries). If prompts still appear outside plan
mode, stop and tell the user rather than asking them to click through each one. Related:
[[feedback-verification-approach]].
