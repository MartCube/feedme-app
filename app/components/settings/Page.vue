<script setup lang="ts">
defineProps<{
  title: string
}>()

// vue-router's live route, not Nuxt's useRoute(): on desktop this renders
// without a NuxtPage, where Nuxt's route object never re-syncs.
const route = useRouter().currentRoute

// The subpage's own icon (same one as its Home list row) leads the title,
// muted, as an extra where-am-I cue.
const icon = computed(() => settingsSections.find(section => section.to === route.value.path)?.icon)

// Swipe right to pop back to the settings home panel; the panel-slide
// transition animates this same root div, so the pop plays as usual.
const panel = useTemplateRef('panel')
const { style: swipeStyle } = useSwipeBack(panel, '/settings')

// Desktop lists the sections in the sidebar, so there's no section list to go
// back to — the top button closes to the reading position instead.
const isDesktop = useIsDesktop()
const closeContent = inject(settingsDrawerCloseKey, () => {})
</script>

<template>
  <!-- touch-none lets vaul own the touch gesture (drag-to-close); revisit
       per page once real content needs touch scrolling. -->
  <div
    ref="panel"
    :style="swipeStyle"
    class="h-full touch-none scroll-host bg-default page-inset"
  >
    <!-- The panel scrolls the full pane width, so its scrollbar sits at the
         pane's edge; the content holds to the form measure inside it — a
         settings list doesn't read better stretched across a wide pane. -->
    <div class="max-w-reading">
      <IconButton
        v-if="isDesktop"
        icon="i-ph-x-bold"
        aria-label="Close settings"
        @click="closeContent"
      />
      <IconButton
        v-else
        icon="i-ph-caret-left-bold"
        to="/settings"
        aria-label="Back to settings"
      />

      <!-- The icon leads, on the text-inset edge, so it sits in line with
           the section labels and row text under it — less 2px, an optical
           correction: a Phosphor glyph sits ~2px inside its box, which left
           it reading as indented past the text below. -->
      <h1 class="mt-lg flex items-center gap-sm text-subtitle tracking-tight">
        <UIcon
          v-if="icon"
          :name="icon"
          class="ml-[calc(var(--spacing-sm)-2px)] size-6 text-muted"
        />
        {{ title }}
      </h1>

      <div class="mt-md flex flex-col gap-lg">
        <slot />
      </div>
    </div>
  </div>
</template>
