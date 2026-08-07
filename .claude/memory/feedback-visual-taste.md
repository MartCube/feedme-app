---
name: feedback-visual-taste
description: FeedMe visual taste — spacing is the default separator but dividers are allowed; never stack separation signals; no glossy rings (codified in docs/design-system.md)
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5d1f3a95-5315-4b3f-84ce-8235b74f7617
  modified: 2026-08-07T17:28:13.069Z
---

Two standing visual rules, codified in `docs/design-system.md` § Color roles → Separation
(the source of truth for tokens and treatments):

- **Spacing first, dividers allowed.** Prefer a gap from the six-step scale as the default
  separator. A hairline divider (`border-default`) is a legitimate tool when spacing alone
  doesn't carry the grouping — long uniform lists, boundaries in tight layouts. **Never
  stack separation signals**: divider + generous gap + card edge is three signals doing one
  job.
- **No glossy edges** — no translucent rings or inner highlights; elevated controls use a
  same-color 1px edge + soft drop shadow (`shadow-elevated`).

**Why:** the user's aesthetic is quiet, low-contrast chrome — minimal, functional, scalable
applied visually. Redundant structural lines and specular highlights read as noise; a single
deliberate line does not.

**How to apply:** default to spacing, reach for a divider when it earns its place, and check
that nothing else is already doing the separating. Check `docs/design-system.md` before
styling. The `design-reviewer` agent enforces this on changed components.
