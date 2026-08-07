---
name: new-component
description: Scaffold a FeedMe component that speaks the design system — correct tokens, no style block, spacing-first separation
disable-model-invocation: true
---

# New FeedMe component

`docs/design-system.md` is the source of truth. This skill is the short form —
when the two disagree, the doc wins.

## Where it goes

| Folder | Holds |
|---|---|
| `app/components/ui/` | Generic, reusable controls (`IconButton`, `Toggle`, `PillButton`) |
| `app/components/feed/` | Post list / card / reading views |
| `app/components/home/` | Home screen bodies |
| `app/components/settings/`, `add/`, `edit/` | Drawer panels and wizard steps |
| `app/components/desktop/` | Three-column shell pieces (≥`lg` only) |

Nuxt auto-imports by path: `app/components/ui/IconButton.vue` → `<IconButton>`,
`app/components/feed/PostCard.vue` → `<FeedPostCard>`. Never write an import for a
component, composable, store, or util — they're all auto-imported.

**Drawers mount in `app/layouts/default.vue`, never as pages under `app/pages/`.**
A nested route remounts the host page. A PreToolUse hook blocks this path.

## Shape

```vue
<script setup lang="ts">
defineProps<{ label: string }>()

const emit = defineEmits<{ select: [uid: string] }>()
</script>

<template>
  <div class="flex flex-col gap-sm">
    <h2 class="text-subtitle tracking-tight">
      {{ label }}
    </h2>
  </div>
</template>
```

- `<script setup lang="ts">` first, `<template>` second.
- **No `<style>` block, ever.** Utilities in the template; anything that can't be a
  utility goes in `app/assets/css/` (`layout.css`, `spacing.css`, `typography.css`,
  `themes.css`, `transitions.css`, `scrollbars.css`) as a token or `@utility`.
- 2-space indent, single quotes, no semicolons — the PostToolUse hook runs
  `eslint --fix` on save, so don't hand-format.

## The vocabulary — 9 color roles, 4 text sizes, 6 spacing steps

Never a raw hex, never `text-sm`/`p-4`, never a one-off `rgba()`. If you need
something outside the scales, that's a design discussion — stop and ask.

**Color:** `bg-default` · `bg-elevated` · `bg-muted` · `text-default`/`text-highlighted` ·
`text-muted` · `text-dimmed` (placeholders/disabled only, never real content) ·
`border-default` · `text-primary`/`bg-primary` · `text-error`

**Type:** `text-title` (screen titles) · `text-subtitle` (section headers, card titles) ·
`text-body` (reading text, rows, buttons) · `text-caption` (dates, meta — usually with
`text-muted`). Two weights only: 400 and 600.

**Spacing:** `2xs` intra-element · `xs` bound pairs · `sm` workhorse (row/card padding) ·
`md` heading→content · `lg` screen inset, section gaps · `xl` bottom runway.

Canonical slots — reach for these before inventing: screen wrapper `page-inset` ·
navbar→title `mt-lg` · heading→content `mt-md` · row padding `py-sm` · card padding
`p-sm` · icon+label `gap-sm` · label+meta `gap-xs` · intra-stack `gap-2xs`.

## Separation and elevation

1. **Spacing is the default separator.** Most groupings read fine on a gap alone.
2. **A hairline divider (`border-default`) is allowed** when spacing doesn't carry the
   grouping — long uniform lists, boundaries in tight layouts.
3. **Never stack both.** Divider + generous gap + card edge is three signals doing one
   job. Pick one.

Elevation is `shadow-elevated` — a same-color 1px edge plus soft drop shadow. **No
translucent rings, no inner highlights, no gloss.**

## Before you call it done

- Screen-level component? Wrap content in `page-inset` — never spell the inset out.
- Interactive? Give it an `aria-label` if the label isn't visible text; the `verify`
  skill drives the app by those labels.
- Desktop-only markup goes behind `lg:` — mobile-first is the base case.
- Never mutate `body`/layout backgrounds from a component.
- Run the `design-reviewer` agent on the diff, then `checker` for lint + typecheck.
