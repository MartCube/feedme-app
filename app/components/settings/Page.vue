<script setup lang="ts">
defineProps<{
  title: string
}>()
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
    </header>

    <div class="mt-md flex flex-col gap-lg">
      <slot />
    </div>
  </div>
</template>
