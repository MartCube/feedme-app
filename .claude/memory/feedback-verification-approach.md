---
name: feedback-verification-approach
description: Frontend has no test harness (lint + typecheck + manual review); the backend gets pytest from roadmap T1 onward
metadata:
  type: feedback
---

**Split by side — don't apply one rule to both.**

**Frontend: no test framework** (only eslint). Verification is `pnpm lint` + `pnpm typecheck` +
driving the change in the running app. **The user manually reviews and tests** the work — don't
build a test-runner step into frontend plans or add a testing stack unprompted.

**Backend: `pytest` + `pytest-django`**, agreed 2026-08-19 and landing in roadmap T1. Tests are
written *with* the task that creates the logic, not afterwards. The reasoning the user accepted:
manual verification works on the frontend because you can see the UI, but backend logic
regresses silently — folder cascades, the polymorphic post-list uid resolver, cursor-pagination
boundaries, token expiry — and is only noticed once data is wrong.

Plans adapt the TDD-centric writing-plans skill accordingly: frontend tasks end with a
lint/typecheck gate + commit + a review checkpoint, not "write a failing test"; backend tasks do
carry real tests in their done-when.

**Agreed future inflection point (frontend):** introduce **Vitest for stores/logic only** (not UI
component tests) when store logic stops being trivial — the folders **cascade rules** (delete
feed/folder, per-folder mute) and saved-state. UI stays manually verified.

**Why:** component tests on an in-flux UI are low ROI; invisible backend state is the opposite.
