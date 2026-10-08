---
paths:
  - "app/**/*.vue"
  - "app/assets/css/**"
---

# Component rules

`docs/design-system.md` is the source of truth; this is the short form — when they disagree, the
doc wins.

## Shape

- `<script setup lang="ts">` first, `<template>` second. **No `<style>` block, ever** — utilities
  in the template; anything that can't be a utility becomes a token or `@utility` in
  `app/assets/css/`.
- Never write an `import` for a component, composable, store, or util — Nuxt auto-imports by
  path (`app/components/feed/PostCard.vue` → `<FeedPostCard>`).
- 2-space indent, single quotes, no semicolons — a PostToolUse hook runs `eslint --fix`; don't
  hand-format.

## Vocabulary — 9 color roles, 4 text sizes, 6 spacing steps

Never a raw hex, never `text-sm` / `p-4`, never a one-off `rgba()`. Outside the scales is a
design discussion — stop and ask. Stock sizes are fine *inside* Nuxt UI `:ui` overrides.

- **Color:** `bg-default` · `bg-elevated` · `bg-muted` · `text-default` / `text-highlighted` ·
  `text-muted` · `text-dimmed` (placeholders and disabled only, never real content) ·
  `border-default` · `text-primary` / `bg-primary` · `text-error`
- **Type:** `text-title` · `text-subtitle` · `text-body` · `text-caption` (usually with
  `text-muted`). Weights 400 and 600 only.
- **Spacing:** `2xs` intra-element · `xs` bound pairs · `sm` row/card padding · `md`
  heading→content · `lg` screen inset and section gaps · `xl` bottom runway. Canonical slots:
  `page-inset` wraps every screen · `mt-lg` navbar→title · `mt-md` heading→content · `py-sm`
  rows · `p-sm` cards · `gap-sm` icon+label · `gap-xs` label+meta · `gap-2xs` intra-stack.
- **Motion:** never write `duration-*` / `ease-*` — timing comes from `app/assets/css/motion.css`
  (a bare `transition-colors` gets 300ms ease-out; slides use `--duration-slide` / `--ease-slide`).
  A new timing is a design discussion.
- A new spacing/type token must also be taught to tailwind-merge in `app.config.ts`
  (`ui.tv.twMergeConfig`) or `:ui` overrides silently lose.

## Separation and elevation

Spacing is the default separator. A hairline `border-default` divider is allowed where spacing
doesn't carry the grouping. **Never stack** divider + generous gap + card edge. Elevation is
`shadow-elevated` — no translucent rings, no inner highlights, no gloss.

## Before you call it done

- Interactive without visible text → `aria-label` (the `verify` skill drives the app by them).
- Desktop-only markup goes behind `lg:` — mobile-first is the base case.
- Never mutate `body` / layout backgrounds from a component; components name roles, themes
  decide appearance.
- Then `design-reviewer` on the diff and `checker` for lint + typecheck.
