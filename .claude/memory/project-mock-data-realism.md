---
name: project-mock-data-realism
description: "Every feed uid deliberately shows ALL mock posts — don't build per-feed filtering while on mock data"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8e94401d-687a-46a5-a529-1e17f00d600c
  modified: 2026-07-27T11:30:38.764Z
---

Every uid (`all`, folders, feeds) showing the full mock post list is deliberate: with ~15
mock posts, real filtering would leave 3-5 posts per list and kill the realistic feel.
The specced `usePostList(uid)` resolver is deferred until real data lands (decided 2026-07-27
during the desktop-layout task).

**Why:** the mock phase exists to evaluate look/feel; sparse lists sabotage that.
**How to apply:** don't "fix" the all-posts behavior or add data-realism features on mock
data; check with the user before any change that would thin out visible content. See
[[feedback-discuss-before-building]].
