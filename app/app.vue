<script setup lang="ts">
// data-theme drives the theme blocks in assets/css/themes.css, data-scrollbar
// the variants in assets/css/scrollbars.css.
const { theme, scrollbarStyle } = storeToRefs(useSettingsStore())
useHead({ htmlAttrs: { 'data-theme': theme, 'data-scrollbar': scrollbarStyle } })
</script>

<template>
  <UApp>
    <NuxtLayout>
      <!-- Reader-flow slide transitions come from route meta, set by middleware/page-slide.global.ts. -->
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
