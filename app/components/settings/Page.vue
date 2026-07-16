<script setup lang="ts">
defineProps<{
  title: string
}>()

const route = useRoute()

// The subpage's own icon (same one as its Home list row) sits muted between
// the back button and the title as an extra where-am-I cue.
const icon = computed(() => settingsSections.find(section => section.to === route.path)?.icon)

// Swipe right to pop back to the settings home panel; the panel-slide
// transition animates this same root div, so the pop plays as usual.
const panel = useTemplateRef('panel')
const { style: swipeStyle } = useSwipeBack(panel, '/settings')
</script>

<template>
  <!-- touch-none lets vaul own the touch gesture (drag-to-close); revisit
       per page once real content needs touch scrolling. -->
  <div
    ref="panel"
    :style="swipeStyle"
    class="h-full touch-none overflow-y-auto bg-default page-inset"
  >
    <IconButton
      icon="i-ph-caret-left-bold"
      to="/settings"
      aria-label="Back to settings"
    />

    <h1 class="mt-lg flex items-center gap-sm text-subtitle tracking-tight text-inset">
      <UIcon
        v-if="icon"
        :name="icon"
        class="size-6 text-muted"
      />
      {{ title }}
    </h1>

    <div class="mt-md flex flex-col gap-lg">
      <slot />
    </div>
  </div>
</template>
