<script setup lang="ts">
// First-run nudge: nothing followed yet, so instead of empty lists point the
// user straight at the add flow. Rendered by the mobile home page and, on
// desktop, in place of the two reading panes.
</script>

<template>
  <div class="mx-auto flex max-w-postlist flex-col items-center justify-center gap-md text-center page-inset">
    <h2 class="text-title tracking-tight">
      Nothing here yet
    </h2>
    <p class="text-body text-muted">
      Follow a website, YouTube channel, or subreddit — new posts land here, all in one calm place.
    </p>
    <BlockButton
      label="Add your first feed"
      icon="i-ph-plus-bold"
      variant="primary"
      @click="navigateTo('/add')"
    />
  </div>
</template>
