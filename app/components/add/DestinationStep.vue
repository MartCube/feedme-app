<script setup lang="ts">
import type { Destination } from '~/stores/feeds'

const emit = defineEmits<{ back: [], choose: [destination: Destination], newFolder: [] }>()

const feedsStore = useFeedsStore()
const { folders } = storeToRefs(feedsStore)

const { selectedFeeds } = useAddFeedWizard()
</script>

<template>
  <!-- touch-none lets vaul own the drag-to-close gesture; revisit once the
       destination list needs real touch scrolling. -->
  <div class="flex h-full touch-none flex-col overflow-y-auto bg-default page-inset">
    <IconButton
      icon="i-ph-caret-left-bold"
      aria-label="Back"
      @click="emit('back')"
    />

    <!-- The feeds being added, so the choice has context. Deliberately quiet
         (label + plain rows, no card): here cards mean "tappable". -->
    <section v-if="selectedFeeds.length">
      <p class="mt-md text-caption text-muted text-inset">
        Adding
      </p>
      <div class="mt-xs flex flex-col gap-2xs text-inset">
        <p
          v-for="feed in selectedFeeds"
          :key="feed.feed_url"
          class="truncate text-body"
        >
          {{ feed.name }}
        </p>
      </div>
    </section>

    <p class="mt-md text-caption text-muted text-inset">
      Add to
    </p>
    <!-- Tapping a destination card commits: every selected feed lands there
         (many feeds → one destination) and the wizard closes. -->
    <ul class="mt-xs flex flex-col gap-sm">
      <li>
        <button
          type="button"
          class="flex w-full items-center gap-sm rounded-2xl bg-elevated p-sm text-left shadow-elevated transition-colors"
          aria-label="Add to top level"
          @click="emit('choose', 'loose')"
        >
          <span class="flex min-w-0 flex-1 items-baseline gap-xs">
            <span class="min-w-0 truncate text-body">Feeds</span>
            <span class="text-caption text-muted">Top level</span>
          </span>
        </button>
      </li>
      <li
        v-for="folder in folders"
        :key="folder.uid"
      >
        <button
          type="button"
          class="flex w-full items-center gap-sm rounded-2xl bg-elevated p-sm text-left shadow-elevated transition-colors"
          :aria-label="`Add to ${folder.name}`"
          @click="emit('choose', folder.uid)"
        >
          <span class="flex min-w-0 flex-1 items-baseline gap-xs">
            <span class="min-w-0 truncate text-body">{{ folder.name }}</span>
            <span class="text-caption text-muted">{{ folder.feed_uids.length }}</span>
          </span>
        </button>
      </li>
      <li>
        <button
          type="button"
          class="flex w-full items-center gap-sm rounded-2xl bg-elevated p-sm text-left shadow-elevated transition-colors"
          @click="emit('newFolder')"
        >
          <UIcon
            name="i-ph-folder-plus-bold"
            class="size-5 shrink-0 text-muted"
          />
          <span class="text-body">New folder</span>
        </button>
      </li>
    </ul>
  </div>
</template>
