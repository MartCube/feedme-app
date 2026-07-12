<script setup lang="ts">
import type { FeedType } from '~/assets/types'

const emit = defineEmits<{ select: [type: FeedType], close: [] }>()

const types: { type: FeedType, label: string, hint: string, icon: string }[] = [
  { type: 'website', label: 'Website', hint: 'Any site or RSS feed', icon: 'i-ph-globe-bold' },
  { type: 'youtube', label: 'YouTube', hint: 'Channels by link or search', icon: 'i-ph-youtube-logo-bold' },
  { type: 'reddit', label: 'Reddit', hint: 'Subreddits by link or search', icon: 'i-ph-reddit-logo-bold' },
]

// Tap feedback: the card's caret flashes primary (same pattern as IconButton),
// staying visible while the panel slides out.
const flashingType = ref<FeedType | null>(null)
let flashTimer: ReturnType<typeof setTimeout> | undefined

function flash(t: FeedType) {
  clearTimeout(flashTimer)
  flashingType.value = t
  flashTimer = setTimeout(() => {
    flashingType.value = null
  }, 250)
}

onScopeDispose(() => clearTimeout(flashTimer))
</script>

<template>
  <!-- touch-none lets vaul own the drag-to-close gesture; revisit once a
       step's content needs real touch scrolling. -->
  <div class="h-full touch-none overflow-y-auto bg-default page-inset">
    <IconButton
      icon="i-ph-x-bold"
      aria-label="Close add feed"
      @click="emit('close')"
    />

    <h1 class="mt-lg text-title tracking-tight ml-4">
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
          @pointerdown="flash(option.type)"
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
            class="size-5 shrink-0 transition-colors duration-300 ease-out"
            :class="flashingType === option.type ? 'text-primary' : 'text-muted'"
          />
        </button>
      </li>
    </ul>
  </div>
</template>
