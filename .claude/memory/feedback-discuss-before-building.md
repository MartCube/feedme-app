---
name: feedback-discuss-before-building
description: "Before building anything: present plan and strategy, discuss, agree — then act. No coding from the very start."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 11c3c55b-a2b8-46b6-a98b-9990eb027d78
---

Before building **anything** — features, UI patterns, architecture, refactors, tooling — first
present the plan and strategy: recommended approach + tradeoff, and an explicit question. Only
write code after the user agrees. This applies even when the request sounds concrete ("add a
button that opens X") — the *how* still needs alignment.

**Why:** the user wants to co-decide direction; building first wastes code and forces redos.

**How to apply:**
- Short proposal first: what, how, why this way, what the alternative was. Then wait.
- For **foundational tech choices** (stack, search engine, auth scheme…) go deeper than a
  short proposal: the user wants a ground-up educational comparison — how each option works
  mechanically, honest steelmanning, costs mapped to *this* product — before locking. He'll
  push back on a bare recommendation with "let's discuss in detail" (backend session,
  2026-07-12: PG-vs-Elasticsearch and JWT-vs-opaque each took a full explainer round).
- When exploring variants of a component: describe options in chat or apply one to the real
  component and iterate — never scaffold comparison/sandbox sections anywhere.
- Simple concrete fixes (typos, obvious bugs, agreed follow-ups) are exempt — execute directly
  per [[feedback-full-file-access]].

Related: [[project-docs-source-of-truth]].
