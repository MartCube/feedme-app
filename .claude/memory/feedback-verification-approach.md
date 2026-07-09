---
name: feedback-verification-approach
description: No test harness yet — verify via lint + typecheck + running the app; user manually reviews and tests
metadata:
  type: feedback
---

FeedMe has **no test framework** (only eslint). For now, verification is: `pnpm lint` +
`pnpm typecheck` + driving the change in the running app. **The user manually reviews and tests**
the work — don't build a test-runner step into plans or add a testing stack unprompted.

Plans adapt the TDD-centric writing-plans skill accordingly: each task ends with a lint/typecheck
gate + commit + a review checkpoint, not "write a failing test".

**Agreed future inflection point:** introduce **Vitest for stores/logic only** (not UI component
tests) when the store logic stops being trivial — specifically the folders **cascade rules**
(delete feed/folder, per-folder mute) and saved-state. UI stays manually verified.

**Why:** component tests on an in-flux UI are low ROI, but pure store/wizard logic is where
automated tests will pay off later.
