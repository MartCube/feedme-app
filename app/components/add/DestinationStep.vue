<script setup lang="ts">
import type { Destination } from '~/stores/feeds'

const emit = defineEmits<{ back: [], choose: [destination: Destination] }>()

const feedsStore = useFeedsStore()
const { folders } = storeToRefs(feedsStore)

const { selectedFeed } = useAddFeedWizard()

// Strip the protocol so the site reads cleanly (css-tricks.com).
function displayUrl(url: string) {
  return url.replace(/^https?:\/\//, '')
}
</script>

<template>
  <!-- touch-none lets vaul own the drag-to-close gesture; revisit once the
       destination list needs real touch scrolling. -->
  <div class="flex h-full touch-none flex-col overflow-y-auto bg-default px-md pt-lg pb-xl">
    <div class="flex items-center gap-sm">
      <IconButton
        icon="i-ph-arrow-left-bold"
        size="sm"
        aria-label="Back"
        @click="emit('back')"
      />
      <h2 class="text-body font-semibold">
        Add to
      </h2>
    </div>

    <!-- The feed being added, so the choice has context. -->
    <div
      v-if="selectedFeed"
      class="mt-md flex flex-col gap-2xs rounded-2xl bg-elevated p-sm shadow-elevated"
    >
      <p class="truncate text-body">
        {{ selectedFeed.name }}
      </p>
      <p class="truncate text-caption text-muted">
        {{ displayUrl(selectedFeed.site_url) }}
      </p>
    </div>

    <ul class="mt-md flex flex-col">
      <li>
        <button
          type="button"
          class="flex w-full items-baseline gap-xs py-sm text-left"
          @click="emit('choose', 'loose')"
        >
          <span class="min-w-0 flex-1 truncate text-body">Feeds</span>
          <span class="text-caption text-muted">Top level</span>
        </button>
      </li>
      <li
        v-for="folder in folders"
        :key="folder.uid"
      >
        <button
          type="button"
          class="flex w-full items-baseline gap-xs py-sm text-left"
          @click="emit('choose', folder.uid)"
        >
          <span class="min-w-0 flex-1 truncate text-body">{{ folder.name }}</span>
          <span class="text-caption text-muted">{{ folder.feed_uids.length }}</span>
        </button>
      </li>
    </ul>
  </div>
</template>
