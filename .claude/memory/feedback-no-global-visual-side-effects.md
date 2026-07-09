---
name: feedback-no-global-visual-side-effects
description: "Never let component work alter global surfaces (body/layout background, html styles) — and beware vaul's body mutations"
metadata:
  type: feedback
---

Component work must never change global surfaces (body/layout backgrounds, html-level styles) as
a side effect — such changes are invisible in the component's diff, and HMR strands stale inline
styles in the user's open tab even after the code is reverted.

**How to apply:**
- Don't use features that mutate `<body>`/global styles (e.g. vaul's `should-scale-background`)
  without asking first.
- After reverting anything that touched global styles, tell the user a hard refresh may be needed.
- The agreed drawer look: dark overlay (`bg-black/60`) only — no background scaling, no shadow.
