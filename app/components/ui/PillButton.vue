<script setup lang="ts">
// Small worded pill button — the header 'Save' affordance. Not a circle (it has
// a word). From tokens: soft elevated surface, primary label when there's a
// draft to commit, dimmed/disabled when clean. Pinned to the IconButton's
// 40px on desktop, so a header pairing the two keeps the top-row axis.
withDefaults(defineProps<{
  label: string
  disabled?: boolean
}>(), {
  disabled: false,
})
</script>

<template>
  <button
    type="button"
    :disabled="disabled"
    class="rounded-full bg-elevated px-md py-xs text-body lg:h-10 lg:py-0 font-medium shadow-elevated transition-colors"
    :class="disabled ? 'text-dimmed' : 'text-primary'"
  >
    {{ label }}
  </button>
</template>
