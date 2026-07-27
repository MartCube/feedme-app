---
name: feedback-ask-dont-assume
description: "When facts are uncertain (environment, symptoms, user setup), ask the user before proceeding — don't assume"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 012d9f59-fadf-43cd-8706-8f02ccbfaf84
  modified: 2026-07-18T18:06:23.633Z
---

When diagnosing or planning and a fact is uncertain (which browser, what exactly was tried, what a symptom looks like), ask the user first instead of assuming and building on the guess. Example: assumed Chrome when the user runs Brave.

**Why:** Assumptions compound — instructions built on a wrong guess waste the user's time and erode trust.

**How to apply:** Before giving diagnostic steps or a plan that depends on unverified facts, use AskUserQuestion (or plain questions) to confirm them. Related: [[feedback-discuss-before-building]].