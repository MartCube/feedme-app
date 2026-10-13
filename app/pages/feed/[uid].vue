<script setup lang="ts">
// Mobile-only passthrough: the desktop shell composes its panes directly
// from the route + stores and never renders NuxtPage (see layouts/default.vue).
// Feed ↔ post ↔ feed page slides come from route meta, set by
// middleware/page-slide.global.ts. The comment lives here, not in the
// template: a template comment beside NuxtPage is a second root node in dev,
// which Nuxt warns breaks navigation between routes.
//
// The div is the element the home ↔ feed slide animates. Without it, that
// transition's hooks pass straight through NuxtPage into the inner feed ↔ post
// <Transition>, whose root is a <Suspense>, and Vue warns "renders non-element
// root" on every navigation. Unpositioned on purpose: a sliding child page's
// absolute inset must still resolve against the layout's relative box.
</script>

<template>
  <div>
    <NuxtPage />
  </div>
</template>
