<script setup lang="ts">
// The header of a foldable sidebar group, rendered as UCollapsible's trigger:
// Reka merges the toggle, aria-expanded and aria-controls onto this button
// (as-child), so it only draws the state it's handed. Styled as the section
// caption used across settings, run the width of the rows under it — the
// hairline is the group's edge, the caret at the far end its state.
defineProps<{
  label: string
  open: boolean
}>()
</script>

<template>
  <button
    type="button"
    class="-mx-sm flex items-center justify-between gap-sm border-b border-default px-sm py-xs text-caption font-semibold uppercase tracking-wide text-muted transition-colors hover-accent"
  >
    {{ label }}
    <UIcon
      name="i-ph-caret-down-bold"
      aria-hidden="true"
      class="size-3 transition-transform"
      :class="open && 'rotate-180'"
    />
  </button>
</template>
