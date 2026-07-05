<script setup lang="ts">
defineProps<{
  title: string
}>()
</script>

<template>
  <!-- touch-none lets vaul own the touch gesture (drag-to-close); revisit
       per page once real content needs touch scrolling. -->
  <div class="h-full touch-none overflow-y-auto bg-default px-8 pt-6 pb-12">
    <header class="flex items-center gap-4">
      <IconButton
        icon="i-ph-caret-left-bold"
        to="/settings"
        aria-label="Back to settings"
      />
      <h2 class="text-xl font-semibold">
        {{ title }}
      </h2>
    </header>

    <div class="mt-10 flex flex-col gap-8">
      <slot />
    </div>
  </div>
</template>
