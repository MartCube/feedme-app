---
name: new-component
description: Scaffold a FeedMe component that speaks the design system — correct tokens, no style block, spacing-first separation
disable-model-invocation: true
---

# New FeedMe component

`docs/design-system.md` is the source of truth; the hard rules are in
`.claude/rules/components.md`, which loads when you read any `.vue` file. **Read one sibling
in the target folder before writing the new file** — that shows the local conventions and
brings the rules into context.

## Where it goes

| Folder | Holds |
|---|---|
| `app/components/ui/` | Generic, reusable controls (`IconButton`, `Toggle`, `PillButton`) |
| `app/components/feed/` | Post list / card / reading views |
| `app/components/home/` | Home screen bodies |
| `app/components/settings/`, `add/`, `edit/` | Drawer panels and wizard steps |
| `app/components/desktop/` | Three-column shell pieces (≥`lg` only) |

Nuxt auto-imports by path: `app/components/ui/IconButton.vue` → `<IconButton>`,
`app/components/feed/PostCard.vue` → `<FeedPostCard>`.

**Drawers mount in `app/layouts/default.vue`, never as pages under `app/pages/`** — a hook
blocks `app/pages/{settings,add,edit}*`.

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

Script first, template second, no `<style>` block, only the 9 / 4 / 6 vocabulary
(`rules/components.md` lists every token and canonical slot). Reach for the canonical slots —
`page-inset`, `mt-lg`, `mt-md`, `py-sm`, `p-sm`, `gap-sm`, `gap-xs`, `gap-2xs` — before
inventing spacing.

## Before you call it done

- Screen-level component? Wrap content in `page-inset` — never spell the inset out.
- Interactive without visible text? `aria-label` — the `verify` skill drives the app by them.
- Desktop-only markup goes behind `lg:` — mobile-first is the base case.
- Run the `design-reviewer` agent on the diff, then `checker` for lint + typecheck.
