<script setup lang="ts">
import type { FeedType } from '~/assets/types'

const emit = defineEmits<{ select: [type: FeedType], close: [] }>()

const types: { type: FeedType, label: string, hint: string, icon: string }[] = [
  { type: 'website', label: 'Website', hint: 'Any site or RSS feed', icon: 'i-ph-globe-bold' },
  { type: 'youtube', label: 'YouTube', hint: 'Channels by link or search', icon: 'i-ph-youtube-logo-bold' },
  { type: 'reddit', label: 'Reddit', hint: 'Subreddits by link or search', icon: 'i-ph-reddit-logo-bold' },
]
</script>

<template>
  <!-- touch-none lets vaul own the drag-to-close gesture; revisit once a
       step's content needs real touch scrolling. -->
  <div class="h-full touch-none overflow-y-auto bg-default px-md pt-lg pb-xl">
    <IconButton
      icon="i-ph-x-bold"
      aria-label="Close add feed"
      @click="emit('close')"
    />

    <h1 class="mt-lg text-title tracking-tight">
      Add feed
    </h1>

    <ul class="mt-md flex flex-col gap-sm">
      <li
        v-for="option in types"
        :key="option.type"
      >
        <button
          type="button"
          class="flex w-full items-center gap-sm rounded-2xl bg-elevated p-sm text-left shadow-elevated transition-colors"
          @click="emit('select', option.type)"
        >
          <UIcon
            :name="option.icon"
            class="size-6 shrink-0 text-muted"
          />
          <span class="min-w-0 flex-1">
            <span class="block text-body">{{ option.label }}</span>
            <span class="block text-caption text-muted">{{ option.hint }}</span>
          </span>
          <UIcon
            name="i-ph-caret-right-bold"
            class="size-5 shrink-0 text-muted"
          />
        </button>
      </li>
    </ul>

    <!-- Folder CTAs — VARIANT A (elevated blocks): pick one, delete the other. -->
    <div class="mt-lg grid grid-cols-2 gap-sm">
      <button
        type="button"
        class="flex flex-col gap-2xs rounded-2xl bg-elevated p-sm text-left shadow-elevated transition-colors"
      >
        <UIcon
          name="i-ph-folder-plus-bold"
          class="size-6 text-muted"
        />
        <span class="text-body">New folder</span>
      </button>
      <button
        type="button"
        class="flex flex-col gap-2xs rounded-2xl bg-elevated p-sm text-left shadow-elevated transition-colors"
      >
        <UIcon
          name="i-ph-pencil-simple-bold"
          class="size-6 text-muted"
        />
        <span class="text-body">Edit folders</span>
      </button>
    </div>

    <!-- Folder CTAs — VARIANT B (quiet rows): pick one, delete the other. -->
    <ul class="mt-lg flex flex-col">
      <li>
        <button
          type="button"
          class="flex w-full items-center gap-sm py-sm text-left text-body"
        >
          <UIcon
            name="i-ph-folder-plus-bold"
            class="size-6 text-muted"
          />
          New folder
        </button>
      </li>
      <li>
        <button
          type="button"
          class="flex w-full items-center gap-sm py-sm text-left text-body"
        >
          <UIcon
            name="i-ph-pencil-simple-bold"
            class="size-6 text-muted"
          />
          Edit folders
        </button>
      </li>
    </ul>
  </div>
</template>
