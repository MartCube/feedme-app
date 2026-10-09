<script setup lang="ts">
// data-theme drives the theme blocks in assets/css/themes.css, data-scrollbar
// the variants in assets/css/scrollbars.css.
const { theme, scrollbarStyle } = storeToRefs(useSettingsStore())
useHead({ htmlAttrs: { 'data-theme': theme, 'data-scrollbar': scrollbarStyle } })

// The account's data is loaded here, on mount, rather than in the route
// middleware: every API call is client-only, so the server renders on empty
// stores, and anything that filled them before hydration would make the two
// renders disagree. onMounted is the first moment that can't happen.
// (Signing in loads them too — see stores/auth.ts.)
const auth = useAuthStore()
onMounted(() => {
  if (auth.signedIn) loadAccount()
})
</script>

<template>
  <!-- Tooltips (ui/IconButton.vue): a short wait so a passing pointer doesn't
       flash them, and keyboard focus only — a tap focuses the button too, and
       on touch that would pop the label up over the thing just pressed. -->
  <UApp :tooltip="{ delayDuration: 400, ignoreNonKeyboardFocus: true }">
    <NuxtLayout>
      <!-- Reader-flow slide transitions come from route meta, set by middleware/page-slide.global.ts. -->
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
