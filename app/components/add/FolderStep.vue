<script setup lang="ts">
const emit = defineEmits<{ back: [], create: [name: string] }>()

// Local on purpose: the panel remounts fresh on every visit, so the name
// never needs a wizard-level reset.
const name = ref('')

function submit() {
  if (!name.value.trim()) return
  emit('create', name.value)
}
</script>

<template>
  <!-- touch-none lets vaul own the drag-to-close gesture. -->
  <div class="flex h-full touch-none flex-col overflow-y-auto bg-default page-inset">
    <header class="flex items-center gap-sm">
      <IconButton
        icon="i-ph-caret-left-bold"
        aria-label="Back"
        @click="emit('back')"
      />
      <h2 class="text-subtitle">
        New folder
      </h2>
    </header>

    <!-- The trailing arrow only appears once there's text — the "disabled
         submit" state for free. Creating pops back to the destination list. -->
    <SearchInput
      v-model="name"
      class="mt-md"
      placeholder="Folder name"
      @submit="submit"
    />
  </div>
</template>
