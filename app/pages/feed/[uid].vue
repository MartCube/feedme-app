<template>
  <!-- Mobile-only passthrough: the desktop shell composes its panes directly
       from the route + stores and never renders NuxtPage (see layouts/default.vue).
       Feed ↔ post slides come from route meta, set by middleware/page-slide.global.ts. -->
  <NuxtPage />
</template>
