<script setup lang="ts">
const emit = defineEmits<{ back: [], forward: [] }>()

const wizard = useAddFeedWizard()
const { type, query, loading, results, selectedFeeds } = wizard

const typeLabel = computed(() => {
  switch (type.value) {
    case 'youtube': return 'YouTube'
    case 'reddit': return 'Reddit'
    default: return 'Website'
  }
})

// Strip the protocol so the result's site reads cleanly (css-tricks.com).
function displayUrl(url: string) {
  return url.replace(/^https?:\/\//, '')
}
</script>

<template>
  <!-- touch-none lets vaul own the drag-to-close gesture; revisit once the
       results list needs real touch scrolling. -->
  <div class="flex h-full touch-none flex-col overflow-y-auto bg-default page-inset">
    <header class="flex items-center gap-sm">
      <IconButton
        icon="i-ph-caret-left-bold"
        aria-label="Back"
        @click="emit('back')"
      />
      <h2 class="text-subtitle">
        {{ typeLabel }}
      </h2>
      <button
        type="button"
        class="ml-auto flex size-12 shrink-0 items-center justify-center rounded-full transition-colors"
        :class="selectedFeeds.length ? 'bg' : 'bg-elevated text-dimmed shadow-elevated'"
        :disabled="!selectedFeeds.length"
        aria-label="Continue"
        @click="emit('forward')"
      >
        <UIcon
          name="i-ph-caret-right-bold"
          class="size-6"
          :class="selectedFeeds.length && 'text-white'"
        />
      </button>
    </header>

    <SearchInput
      v-model="query"
      class="mt-md"
      placeholder="Paste a link or search…"
      paste
      @submit="wizard.search()"
    />

    <ul
      v-if="loading"
      class="mt-md flex flex-col"
    >
      <li
        v-for="n in 3"
        :key="n"
        class="flex flex-col gap-2xs py-sm"
      >
        <USkeleton class="h-4 w-2/3" />
        <USkeleton class="h-3 w-1/3" />
      </li>
    </ul>

    <!-- Tapping anywhere on a card toggles its checkbox — multi-select, the
         header's forward button advances once at least one feed is picked. -->
    <ul
      v-else-if="results.length"
      class="mt-md flex flex-col gap-sm"
    >
      <li
        v-for="result in results"
        :key="result.feed_url"
      >
        <button
          type="button"
          class="flex w-full items-center gap-sm rounded-2xl bg-elevated p-sm text-left shadow-elevated transition-colors"
          :aria-pressed="wizard.isSelected(result)"
          :aria-label="`Select ${result.name}`"
          @click="wizard.toggleFeed(result)"
        >
          <span class="min-w-0 flex-1">
            <span class="block truncate text-body">{{ result.name }}</span>
            <span class="block truncate text-caption text-muted">{{ displayUrl(result.site_url) }}</span>
          </span>
          <!-- Page-bg circle reads as a well punched into the card; checking
               only drops a primary checkmark in, nothing else changes. -->
          <span
            class="flex size-10 shrink-0 items-center justify-center"
            aria-hidden="true"
          >
            <span class="flex size-8 items-center justify-center rounded-full bg-default">
              <UIcon
                v-if="wizard.isSelected(result)"
                name="i-ph-check-bold"
                class="size-5 text-primary"
              />
            </span>
          </span>
        </button>
      </li>
    </ul>
  </div>
</template>
