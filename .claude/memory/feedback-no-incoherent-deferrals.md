---
name: feedback-no-incoherent-deferrals
description: Don't defer a small visible piece when its architecture must be built anyway — that leaves a gap, not a saving
metadata:
  node_type: memory
  type: feedback
---

Before proposing to defer a piece of work to a later task, check what deferring actually
saves. If the surrounding architecture has to be built either way, deferring only the visible
piece leaves an incoherent gap — and the later task inherits extra work *plus* removing the
temporary bypass.

**Why:** the user pushes back on deferrals that optimise for a shorter session over a coherent
result, and asks for the reasoning ("why you not to build simple X for now, explain"). A weak
recommendation defended rather than re-examined costs more trust than the deferral saves.
(Backend roadmap, 2026-08-19: deferring the login screen would still have required the auth
store, `$fetch` wrapper, route middleware and 401 handling — so it saved one small page while
leaving middleware with nowhere to redirect.)

**How to apply:** build the complete coherent slice, and make the temporary part a *swappable
detail inside it* (a dev-token field where the real button will go) rather than a bypass
around it. When challenged on a recommendation, steelman the other side properly and say
plainly if it wins.

Distinct from [[feedback-minimal-machinery]], which cuts unjustified **new** abstractions —
this one cuts incoherent **gaps**. They don't conflict: the first says don't build what isn't
needed, the second says don't half-build what is. Related: [[feedback-discuss-before-building]].
