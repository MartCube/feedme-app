---
name: feedback-naming-taste
description: "Naming: no enterprise-speak; backend and frontend must share the same nouns for the same things."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 11c3c55b-a2b8-46b6-a98b-9990eb027d78
---

The user rejects enterprise-flavored entity names ("Subscription" was vetoed hard) and wants
backend and frontend to use **the same noun for the same concept**. Since 2026-10-08 a `Feed` is
a user's named group of `Source`s (one or many) and `Source` is user-facing; folders were
retired as a concept, so don't reintroduce a grouping noun above Feed. The join row is
`FeedSource` in code only.

**Why:** translation layers between API vocabulary and UI vocabulary create permanent
confusion; naming was important enough to the user to open the backend session with it.

**How to apply:** when introducing a new entity, start from what the frontend/docs already
call it; propose plain product words, not architecture-pattern words. Check
`docs/backend.md`'s vocabulary table before naming anything new.

Related: [[feedback-discuss-before-building]], [[project-docs-source-of-truth]].
