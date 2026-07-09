<script setup lang="ts">
import type { FeedCandidate } from '~/assets/types'

const emit = defineEmits<{ back: [], pick: [feed: FeedCandidate] }>()

const wizard = useAddFeedWizard()
const { type, query, loading, results } = wizard

const typeLabel = computed(() => {
  switch (type.value) {
    case 'youtube': return 'YouTube'
    case 'reddit': return 'Reddit'
    default: return 'Website'
  }
})

// The Paste chip shows only while the input is focused and still empty — once
// there's text (typed or pasted) it gives way to the search submit arrow.
const focused = ref(false)

// Browsers block silent clipboard reads, so the chip reads on tap (a user
// gesture). mousedown.prevent (on the button) keeps the input focused through
// the click, so focusout doesn't remove the chip before the tap lands.
async function paste() {
  try {
    const text = await navigator.clipboard.readText()
    if (text) query.value = text
  }
  catch {
    // clipboard blocked/empty — the user can type instead
  }
}

// Strip the protocol so the result's site reads cleanly (css-tricks.com).
function displayUrl(url: string) {
  return url.replace(/^https?:\/\//, '')
}
</script>

<template>
  <!-- touch-none lets vaul own the drag-to-close gesture; revisit once the
       results list needs real touch scrolling. -->
  <div class="flex h-full touch-none flex-col overflow-y-auto bg-default px-md pt-lg pb-xl">
    <div class="flex items-center gap-sm">
      <IconButton
        icon="i-ph-arrow-left-bold"
        size="sm"
        aria-label="Back"
        @click="emit('back')"
      />
      <h2 class="text-body font-semibold">
        {{ typeLabel }}
      </h2>
    </div>

    <form
      class="mt-md"
      @submit.prevent="wizard.search()"
    >
      <UInput
        v-model="query"
        placeholder="Paste a link or search…"
        size="xl"
        class="w-full"
        @focusin="focused = true"
        @focusout="focused = false"
      >
        <template #trailing>
          <UButton
            v-if="query"
            icon="i-ph-arrow-right-bold"
            color="neutral"
            variant="ghost"
            size="sm"
            type="submit"
            aria-label="Search"
          />
          <UButton
            v-else-if="focused"
            label="Paste"
            color="neutral"
            variant="soft"
            size="sm"
            @mousedown.prevent
            @click="paste"
          />
        </template>
      </UInput>
    </form>

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

    <ul
      v-else-if="results.length"
      class="mt-md flex flex-col"
    >
      <li
        v-for="result in results"
        :key="result.feed_url"
        class="flex items-center gap-sm py-sm"
      >
        <div class="min-w-0 flex-1">
          <p class="truncate text-body">
            {{ result.name }}
          </p>
          <p class="truncate text-caption text-muted">
            {{ displayUrl(result.site_url) }}
          </p>
        </div>
        <IconButton
          icon="i-ph-plus-bold"
          size="sm"
          aria-label="Add feed"
          @click="emit('pick', result)"
        />
      </li>
    </ul>
  </div>
</template>
