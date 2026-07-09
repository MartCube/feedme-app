---
name: feedback-visual-taste
description: "FeedMe visual taste — no divider lines in lists, no glossy rings; spacing and soft shadows only (codified in docs/design-system.md)"
metadata:
  type: feedback
---

Two standing visual rules, codified in `docs/design-system.md` (the source of truth for tokens
and treatments):

- **No divider lines in lists** — lists separate by spacing, not `border-b` hairlines.
- **No glossy edges** — no translucent rings or inner highlights; elevated controls use a
  same-color 1px edge + soft drop shadow (`shadow-elevated`).

**Why:** the user's aesthetic is quiet, low-contrast chrome — minimal, functional, scalable
applied visually. Visible structural lines and specular highlights read as noise.

**How to apply:** default to spacing over borders and soft shadows over rings. If a design idea adds
visible lines or gloss, flag it and ask first. Check `docs/design-system.md` before styling.
