<script setup lang="ts">
// data-theme drives the theme blocks in assets/css/themes.css.
const { theme } = storeToRefs(useSettingsStore())
useHead({ htmlAttrs: { 'data-theme': theme } })
</script>

<template>
  <UApp>
    <NuxtLayout>
      <!-- Reader-flow slide transitions come from route meta, set by middleware/page-slide.global.ts. -->
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
