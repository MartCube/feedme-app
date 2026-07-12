<script setup lang="ts">
defineProps<{
  title: string
}>()

const route = useRoute()

// The subpage's own icon (same one as its Home list row) sits muted between
// the back button and the title as an extra where-am-I cue.
const icon = computed(() => settingsSections.find(section => section.to === route.path)?.icon)
</script>

<template>
  <!-- touch-none lets vaul own the touch gesture (drag-to-close); revisit
       per page once real content needs touch scrolling. -->
  <div class="h-full touch-none overflow-y-auto bg-default page-inset">
    <header class="flex items-center gap-sm">
      <IconButton
        icon="i-ph-caret-left-bold"
        to="/settings"
        aria-label="Back to settings"
      />
      <UIcon
        v-if="icon"
        :name="icon"
        class="size-6 text-muted"
      />
      <h2 class="text-subtitle">
        {{ title }}
      </h2>
    </header>

    <div class="mt-md flex flex-col gap-lg">
      <slot />
    </div>
  </div>
</template>
