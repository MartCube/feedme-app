---
name: feedback-one-integration-per-task
description: "A task scoped to one integration (YouTube / Reddit / website) stays inside it — don't design for sibling integrations or justify a field by a future task"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3562375a-4d9f-4710-9c40-4b60503e3de1
  modified: 2026-09-11T14:56:29.168Z
---

When a task covers one integration, keep the design inside that integration. Don't propose
unifying result shapes across YouTube / Reddit / website, and don't justify a new field or
component by "the next task will want it too". Whether the types share a shape is decided
later, by comparing real results from each — not predicted up front.

**Why:** speculative cross-type design is scope the user didn't ask for, and it argues from
a future task instead of the one at hand. It also reads as noise when the sibling
integration isn't even part of the current API surface.

**How to apply:** describe behaviour only for the type being built; leave the other types'
behaviour explicitly untouched and say so. If a shared shape looks likely, note it as a
later decision rather than building for it. Relates to [[feedback-minimal-machinery]] and
[[feedback-no-incoherent-deferrals]] — this is the scope-widening twin of those.
