<script setup lang="ts">
import type { FeedType } from '~/assets/types'

const emit = defineEmits<{ select: [type: FeedType] }>()

const types: { type: FeedType, label: string, hint: string, icon: string }[] = [
  { type: 'website', label: 'Website', hint: 'Any site or RSS feed', icon: 'i-ph-globe-bold' },
  { type: 'youtube', label: 'YouTube', hint: 'Channels by link or search', icon: 'i-ph-youtube-logo-bold' },
  { type: 'reddit', label: 'Reddit', hint: 'Subreddits by link or search', icon: 'i-ph-reddit-logo-bold' },
]
</script>

<template>
  <div>
    <h1 class="text-title tracking-tight">
      Add feed
    </h1>

    <ul class="mt-8 flex flex-col gap-2">
      <li
        v-for="option in types"
        :key="option.type"
      >
        <button
          type="button"
          class="flex w-full items-center gap-4 rounded-2xl bg-elevated px-4 py-4 text-left shadow-elevated transition-colors"
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
  </div>
</template>
