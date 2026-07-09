<script setup lang="ts">
import type { Destination } from '~/stores/feeds'

const emit = defineEmits<{ back: [], choose: [destination: Destination] }>()

const feedsStore = useFeedsStore()
const { folders } = storeToRefs(feedsStore)

const { selectedFeed } = useAddFeedWizard()

const { selectedUid, select } = useTapSelection()

// Strip the protocol so the site reads cleanly (css-tricks.com).
function displayUrl(url: string) {
  return url.replace(/^https?:\/\//, '')
}
</script>

<template>
  <!-- touch-none lets vaul own the drag-to-close gesture; revisit once the
       destination list needs real touch scrolling. -->
  <div class="flex h-full touch-none flex-col overflow-y-auto bg-default px-md pt-lg pb-xl">
    <header class="flex items-center gap-sm">
      <IconButton
        icon="i-ph-caret-left-bold"
        aria-label="Back"
        @click="emit('back')"
      />
      <h2 class="text-subtitle">
        Add to
      </h2>
    </header>

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

    <!-- Tapping a row only flashes it; the plus commits the add. Keeps the
         door open for multi-select (many feeds into many folders) later. -->
    <ul class="mt-md flex flex-col">
      <li
        class="-mx-sm flex items-center gap-sm rounded-2xl px-sm py-sm transition-colors"
        :class="selectedUid === 'loose' && 'bg-elevated shadow-elevated'"
        @pointerdown="select('loose')"
      >
        <div class="flex min-w-0 flex-1 items-baseline gap-xs">
          <span class="min-w-0 truncate text-body">Feeds</span>
          <span class="text-caption text-muted">Top level</span>
        </div>
        <IconButton
          icon="i-ph-plus-bold"
          size="sm"
          aria-label="Add to top level"
          @click="emit('choose', 'loose')"
        />
      </li>
      <li
        v-for="folder in folders"
        :key="folder.uid"
        class="-mx-sm flex items-center gap-sm rounded-2xl px-sm py-sm transition-colors"
        :class="selectedUid === folder.uid && 'bg-elevated shadow-elevated'"
        @pointerdown="select(folder.uid)"
      >
        <div class="flex min-w-0 flex-1 items-baseline gap-xs">
          <span class="min-w-0 truncate text-body">{{ folder.name }}</span>
          <span class="text-caption text-muted">{{ folder.feed_uids.length }}</span>
        </div>
        <IconButton
          icon="i-ph-plus-bold"
          size="sm"
          :aria-label="`Add to ${folder.name}`"
          @click="emit('choose', folder.uid)"
        />
      </li>
    </ul>
  </div>
</template>
