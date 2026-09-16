---
name: feedback-strategy-decisions
description: "How to run an architecture/strategy discussion with this user — judge options on \"best for the product\", not least code; when they say it's a lot to take in, collapse to one plain pick"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6c51f4e2-caf5-4166-9dfc-39ef82cc03c2
  modified: 2026-09-15T21:35:11.834Z
---

When the user asks for a strategy (storage, infra, pipelines), two rules:

1. **"Best for us" beats "least code."** They said so explicitly (images strategy, 2026-09-15):
   a recommendation justified mainly by being smaller gets pushed back on. Weigh quality,
   durability, scale path and ops burden for a solo dev; say which one wins and why. Their
   stated frame: works really nicely for ≤100 users now, buy capacity with money later, never
   box the app in.
2. **Watch for overload.** Wide pros/cons tables are welcome *once*; when they say "a lot to
   ingest" or "help me choose", stop listing options — give one pick in plain language, what
   they'd see in practice, and one question at most. Splitting a decision into independent
   axes (e.g. "who resizes" vs "do we keep a copy") and showing that two options are the same
   plan in a different order is what unblocked them.

**Why:** the discussion looped three times while I re-presented option matrices; the reframing
"same plan, bucket in task 1 or task 2" is what got a decision.

**How to apply:** lead with the recommendation and the one deciding criterion; keep the full
comparison behind it for reference. Related: [[feedback-discuss-before-building]],
[[user-backend-vs-frontend-depth]], [[reference-crowdfeed]].
