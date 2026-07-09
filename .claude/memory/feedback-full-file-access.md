---
name: feedback-full-file-access
description: "Work directly: blanket read/edit access to all project files, no permission asking, no subagent ceremony for simple work"
metadata:
  type: feedback
---

Blanket permission: read and edit any file in the feedme project (including `.claude/` and the
memory dir) without asking. Only file deletion and dangerous commands stay behind confirmation.

No multi-agent/task ceremony for simple work: for a list of concrete fixes — even 5–7 of them —
edit directly, verify once (lint/build/quick check), done. Reserve subagent orchestration for
genuinely large plans the user asked to run that way ([[feedback-model-policy]] governs models).

**Why:** permission prompts and orchestration overhead interrupt the user for decisions they've
already made. If permission prompts reappear for paths outside the project, that's a *settings*
fix (`.claude/settings.local.json` additionalDirectories/allow rules), not an apology.

Still respect standing content rules: [[project-docs-source-of-truth]],
[[feedback-discuss-before-building]].
