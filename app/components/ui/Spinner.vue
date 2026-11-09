<script setup lang="ts">
// The app's one loading mark, beside whatever started the wait: the wordmark
// for any API call (HomeFeedList), the add wizard's step title for its own
// search, preview and add — on a wide screen the wordmark is a long way from
// the column you're working in. Debounced so a wait that ends inside 150ms
// never flashes it. One component so the custom spinner
// (pending_tasks/custom-spinner.md) lands in one place.
const props = defineProps<{ active: boolean }>()

const shown = refDebounced(toRef(props, 'active'), 150)
</script>

<template>
  <!-- Decorative: whatever is waiting says so itself (aria-busy on the
       Preview chip, the disabled Add). -->
  <UIcon
    v-if="shown"
    name="i-ph-circle-notch-bold"
    aria-hidden="true"
    class="size-5 animate-spin text-primary"
  />
</template>
