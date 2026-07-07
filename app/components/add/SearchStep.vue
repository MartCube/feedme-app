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

// Browsers block silent clipboard reads, so the Paste chip reads on tap (a user
// gesture). It shows only while the input is empty.
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
  <div class="flex flex-col">
    <div class="flex items-center gap-2">
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
      class="mt-6"
      @submit.prevent="wizard.search()"
    >
      <UInput
        v-model="query"
        placeholder="Paste a link or search…"
        size="xl"
        class="w-full"
      >
        <template #trailing>
          <UButton
            v-if="!query"
            label="Paste"
            color="neutral"
            variant="soft"
            size="sm"
            @click="paste"
          />
          <UButton
            v-else
            icon="i-ph-arrow-right-bold"
            color="neutral"
            variant="ghost"
            size="sm"
            type="submit"
            aria-label="Search"
          />
        </template>
      </UInput>
    </form>

    <ul
      v-if="loading"
      class="mt-6 flex flex-col gap-5"
    >
      <li
        v-for="n in 3"
        :key="n"
        class="flex flex-col gap-2"
      >
        <USkeleton class="h-4 w-2/3" />
        <USkeleton class="h-3 w-1/3" />
      </li>
    </ul>

    <ul
      v-else-if="results.length"
      class="mt-4 flex flex-col"
    >
      <li
        v-for="result in results"
        :key="result.feed_url"
        class="flex items-center gap-3 py-3"
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
