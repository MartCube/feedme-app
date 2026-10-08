<script setup lang="ts">
// Mobile-only passthrough: the desktop shell composes its panes directly
// from the route + stores and never renders NuxtPage (see layouts/default.vue).
// Feed ↔ post ↔ feed page slides come from route meta, set by
// middleware/page-slide.global.ts. The comment lives here, not in the
// template: a template comment beside NuxtPage is a second root node in dev,
// which Nuxt warns breaks navigation between routes.
</script>

<template>
  <NuxtPage />
</template>
