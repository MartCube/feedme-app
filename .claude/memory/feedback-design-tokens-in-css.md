---
name: feedback-design-tokens-in-css
description: "Design-system scales (spacing, type, etc.) must be real @theme tokens in a dedicated CSS file, not documentation-only conventions"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c47e10fe-ecda-483e-b0bd-6a6c6039a70e
---

Design-system scales must live as real `@theme` tokens in a dedicated file under
`app/assets/css/` (imported by `main.css`), mirroring `typography.css` — not as a
"documented convention over raw utilities." When proposing a new scale, default to the
token-file approach; don't offer doc-only conventions as the primary option.

**Why:** the user expects tokens to have a single source of truth in CSS (like the type
scale), and reacted to a doc-only spacing plan with "I was expecting a css file where we
will write the spacing." Tailwind v4 `--spacing-*` / `--text-*` tokens generate named
utilities (`p-sm`, `gap-md`, `mt-lg`), which is the shape they want.

**How to apply:** put the scale in its own `*.css` with an `@theme static` block, import
it in `main.css`, and use the named utilities in components (not the numeric Tailwind
steps). See [[feedback-visual-taste]] and [[project-docs-source-of-truth]].
