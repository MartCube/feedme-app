<script setup lang="ts">
defineProps<{
  title: string
}>()

const route = useRoute()

// The subpage's own icon (same one as its Home list row) sits muted at the
// far right of the header as an extra where-am-I cue.
const icon = computed(() => settingsSections.find(section => section.to === route.path)?.icon)
</script>

<template>
  <!-- touch-none lets vaul own the touch gesture (drag-to-close); revisit
       per page once real content needs touch scrolling. -->
  <div class="h-full touch-none overflow-y-auto bg-default px-md pt-lg pb-xl">
    <header class="flex items-center gap-sm">
      <IconButton
        icon="i-ph-caret-left-bold"
        to="/settings"
        aria-label="Back to settings"
      />
      <h2 class="text-subtitle">
        {{ title }}
      </h2>
      <UIcon
        v-if="icon"
        :name="icon"
        class="ml-auto size-6 text-muted"
      />
    </header>

    <div class="mt-md flex flex-col gap-lg">
      <slot />
    </div>
  </div>
</template>
