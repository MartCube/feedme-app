<script setup lang="ts">
import type { Destination } from '~/stores/feeds'

const emit = defineEmits<{ back: [], choose: [destination: Destination] }>()

const feedsStore = useFeedsStore()
const { folders } = storeToRefs(feedsStore)
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
        Add to
      </h2>
    </div>

    <ul class="mt-6 flex flex-col">
      <li>
        <button
          type="button"
          class="flex w-full items-baseline gap-2 py-4 text-left"
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
          class="flex w-full items-baseline gap-2 py-4 text-left"
          @click="emit('choose', folder.uid)"
        >
          <span class="min-w-0 flex-1 truncate text-body">{{ folder.name }}</span>
          <span class="text-caption text-muted">{{ folder.feed_uids.length }}</span>
        </button>
      </li>
    </ul>
  </div>
</template>
