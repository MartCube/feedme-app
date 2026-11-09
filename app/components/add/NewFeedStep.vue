<script setup lang="ts">
const emit = defineEmits<{
  back: []
  close: []
  create: [input: { name: string, description: string, removeFromOrigin: boolean }]
}>()

const { picked, origin, adding, error, busy } = useAddFeedWizard()

// Prefilled with the source's name: a one-source feed is the common
// case, and it should cost one tap. Local on purpose — the panel remounts
// fresh on every visit, so the drafts never need a wizard-level reset. A
// blank description takes the source's own.
const name = ref(picked.value?.name ?? '')
const description = ref('')
// Only offered when the source came from a feed (a source page's "New feed
// from this source"). Off by default: keeping it in both is the reversible choice.
const removeFromOrigin = ref(false)

function submit() {
  if (!name.value.trim() || adding.value) return
  emit('create', { name: name.value, description: description.value, removeFromOrigin: removeFromOrigin.value })
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
      <!-- Opened from a source page there is no step behind this one. -->
      <IconButton
        v-if="!origin"
        icon="i-ph-caret-left-bold"
        aria-label="Back"
        @click="emit('back')"
      />
    </header>

    <h1 class="mt-lg text-title tracking-tight">
      New feed<Spinner
        :active="busy"
        class="ms-sm align-middle"
      />
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

    <UInput
      v-model="description"
      class="mt-sm w-full"
      placeholder="What this feed is for"
      aria-label="Feed description"
      :ui="{ base: 'px-sm py-sm text-body rounded-2xl transition' }"
      @keydown.enter="submit"
    />

    <!-- The whole row toggles, like a settings row; the switch shows the state. -->
    <label
      v-if="origin"
      class="mt-md flex cursor-pointer items-center justify-between gap-sm rounded-2xl px-sm py-sm text-body transition-colors hover-accent"
    >
      <span class="min-w-0 truncate">Remove from {{ origin.feedName }}</span>
      <Toggle
        v-model="removeFromOrigin"
        :aria-label="`Remove from ${origin.feedName}`"
      />
    </label>

    <p
      v-if="error"
      class="mt-xs text-caption text-error text-inset"
    >
      {{ error }}
    </p>

    <!-- The arrow in the name field does the same; this is the obvious way. -->
    <BlockButton
      class="mt-xl"
      variant="primary"
      :label="adding ? 'Creating…' : 'Create feed'"
      :disabled="!name.trim() || adding"
      @click="submit"
    />
  </div>
</template>
