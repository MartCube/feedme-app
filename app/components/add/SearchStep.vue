<script setup lang="ts">
import type { FeedCandidate } from '~/assets/types'

const emit = defineEmits<{ back: [], close: [], pick: [candidate: FeedCandidate] }>()

const wizard = useAddFeedWizard()
const { type, query, loading, results, searched, error, busy } = wizard

// Heading label/icon and placeholder all come from the type card the user
// just tapped (website when the type is somehow unset).
const typeMeta = computed(() => feedTypes.find(option => option.type === type.value) ?? feedTypes[0]!)
</script>

<template>
  <!-- touch-none lets vaul own the drag-to-close gesture; revisit once the
       results list needs real touch scrolling. -->
  <div class="flex h-full touch-none flex-col scroll-host bg-default page-inset *:max-w-reading">
    <!-- Close then Back, as a bound pair like the post's actions. No forward
         button: one source per pass, so tapping a result is the way on. -->
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

    <h1 class="mt-lg flex items-center gap-sm text-title tracking-tight">
      <UIcon
        :name="typeMeta.icon"
        class="size-6 text-muted"
      />
      {{ typeMeta.label }}
      <Spinner :active="busy" />
    </h1>

    <SearchInput
      v-model="query"
      class="mt-md"
      :placeholder="typeMeta.placeholder"
      paste
      autofocus
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

    <ul
      v-else-if="results.length"
      class="mt-md flex flex-col gap-sm"
    >
      <AddResultCard
        v-for="result in results"
        :key="result.feed_url"
        :result="result"
        @pick="emit('pick', result)"
      />
    </ul>

    <!-- /discover resolves links, channels and subreddits, and searches YouTube by name;
         a keyword under the other cards finds nothing until T11d searches our own
         catalog. Saying so beats a blank panel. -->
    <p
      v-else-if="searched"
      class="mt-md text-body text-muted"
    >
      Nothing found. Try pasting a link.
    </p>

    <!-- The feed page's Add source commits straight from this step (it already
         knows the feed), so a refused add has to be able to say so here too. -->
    <p
      v-if="error"
      class="mt-xs text-caption text-error text-inset"
    >
      {{ error }}
    </p>
  </div>
</template>
