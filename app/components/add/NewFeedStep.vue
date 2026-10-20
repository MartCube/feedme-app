<script setup lang="ts">
const emit = defineEmits<{ back: [], close: [], create: [name: string] }>()

const { selectedFeeds, adding, error } = useAddFeedWizard()

// Prefilled with the first source's name: a one-source feed is the common
// case, and it should cost one tap. Local on purpose — the panel remounts
// fresh on every visit, so the name never needs a wizard-level reset. The
// description is the source's own until the feed page edits it.
const name = ref(selectedFeeds.value[0]?.name ?? '')

function submit() {
  if (!name.value.trim() || adding.value) return
  emit('create', name.value)
}
</script>

<template>
  <!-- touch-none lets vaul own the drag-to-close gesture. -->
  <div class="flex h-full touch-none flex-col scroll-host bg-default page-inset *:max-w-reading">
    <header class="flex items-center gap-xs">
      <IconButton
        icon="i-ph-x-bold"
        aria-label="Close add feed"
        @click="emit('close')"
      />
      <IconButton
        icon="i-ph-caret-left-bold"
        aria-label="Back"
        @click="emit('back')"
      />
    </header>

    <h1 class="mt-lg text-title tracking-tight">
      New feed
    </h1>

    <!-- The trailing arrow only appears once there's text — the "disabled
         submit" state for free. Creating closes the wizard. -->
    <SearchInput
      v-model="name"
      class="mt-md"
      placeholder="Feed name"
      autofocus
      @submit="submit"
    />

    <p
      v-if="error"
      class="mt-xs text-caption text-error text-inset"
    >
      {{ error }}
    </p>
  </div>
</template>
