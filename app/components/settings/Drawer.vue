<script setup lang="ts">
import type { Component } from 'vue'
import { SettingsAbout, SettingsAccount, SettingsAppearance, SettingsHome, SettingsReport } from '#components'

// Hosts the settings bottom sheet. The settings URLs render the home route
// (see the pages:extend hook in nuxt.config) and the panels are plain
// components switched here — no nested NuxtPage. Nested route pages remount
// their parent page on navigation (nuxt#13094), which replayed the drawer's
// enter animation; with one route + local panels nothing can remount.
const route = useRoute()
const open = ref(false)

const panels: Record<string, Component> = {
  '/settings': SettingsHome,
  '/settings/about': SettingsAbout,
  '/settings/account': SettingsAccount,
  '/settings/appearance': SettingsAppearance,
  '/settings/report': SettingsReport,
}

const activePanel = computed(() => panels[route.path])
const onSettings = computed(() => Boolean(activePanel.value))

// Slide direction between panels: deeper pushes in from the right, shallower
// pops back out. 'none' at the drawer's open/close boundary — those moments
// are covered by the drawer's own animation.
const slide = ref<'push' | 'pop' | 'none'>('none')
watch(() => route.path, (to, from) => {
  if (!panels[to] || !panels[from]) {
    slide.value = 'none'
    return
  }
  const depth = (path: string) => path.split('/').filter(Boolean).length
  slide.value = depth(to) < depth(from) ? 'pop' : 'push'
})

// Direction rides on live CSS variables under a FIXED transition name
// (.panel-slide-* and the .settings-panels defaults live in main.css).
// Switching the name doesn't work: Vue binds leave hooks to the name a panel
// *entered* under, so the leaving panel would animate with a stale direction
// (or not at all). Variables are read when the leave actually runs.
const slideVars = computed(() => {
  if (slide.value === 'pop') {
    return { '--panel-enter-from': '-25%', '--panel-leave-to': '100%', '--panel-leave-z': '1' }
  }
  if (slide.value === 'push') {
    return { '--panel-enter-from': '100%', '--panel-leave-to': '-25%', '--panel-enter-z': '1' }
  }
  return {}
})

// vaul emits animationEnd(false) for its initial closed state — only a close
// that follows a completed open animation should navigate home.
const hasOpened = ref(false)

watch(onSettings, (on) => {
  open.value = on
})

onMounted(() => {
  if (onSettings.value) {
    open.value = true
  }
})

provide(settingsDrawerCloseKey, () => {
  open.value = false
})

function onAnimationEnd(isOpen: boolean) {
  if (isOpen) {
    hasOpened.value = true
  }
  else if (hasOpened.value && onSettings.value) {
    navigateTo('/')
  }
}
</script>

<template>
  <UDrawer
    v-model:open="open"
    :handle="false"
    :ui="{
      // overflow-hidden clips the square-cornered panels to the sheet's
      // rounded top corners.
      content: 'mt-0 h-full max-h-full overflow-hidden',
      container: 'grow gap-0 p-0 overflow-hidden',
      body: 'relative overflow-hidden',
    }"
    @animation-end="onAnimationEnd"
  >
    <template #body>
      <div
        class="settings-panels h-full"
        :style="slideVars"
      >
        <Transition name="panel-slide">
          <component
            :is="activePanel"
            v-if="activePanel"
            :key="route.path"
          />
        </Transition>
      </div>
    </template>
  </UDrawer>
</template>
