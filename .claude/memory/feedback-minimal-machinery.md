---
name: feedback-minimal-machinery
description: User challenges every new abstraction — justify each new composable/util in detail or cut it
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8e94401d-687a-46a5-a529-1e17f00d600c
  modified: 2026-07-27T11:30:44.880Z
---

When planning, the user pushes back on anything that smells like over-engineering ("we want
simple, functional, scalable work, especially at the start of a task") and expects a detailed
why for each new composable/util/store field before accepting it.

**Why:** minimalism is the product; unjustified machinery erodes trust in the plan.
**How to apply:** in plans, separate "moves existing code" from "genuinely new code", keep the
new-code list tiny, and for each new abstraction explain what breaks without it (e.g. the
useIsDesktop discussion: CSS can't stop JS drawers, v-if needs an SSR-safe boolean). Related:
[[feedback-discuss-before-building]], [[feedback-ask-dont-assume]].
