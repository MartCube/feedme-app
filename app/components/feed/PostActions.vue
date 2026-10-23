<script setup lang="ts">
import type { Post } from '~/assets/types'

// The post's actions — Copy link, Open source and Save — as one set, because
// the mobile navbar and the desktop post pane render exactly the same buttons.
// The host owns the save state (it comes from usePost), so this only emits.
// Rendered before the post arrives, so the row doesn't blink out and back on
// every post change: until then the buttons look the same and do nothing —
// Open source has no URL to go to, Copy link nothing to copy, and usePost's
// toggleSave already ignores a press with no post.
// `target` and `rel` fall through IconButton to UButton, which renders an
// absolute URL as a plain <a> and adds rel="noopener noreferrer" itself.
const props = defineProps<{ post: Post | null, saved: boolean }>()
defineEmits<{ toggleSave: [] }>()

// Copies the source URL, not the FeedMe one: a FeedMe link needs an account to
// open, so it's useless to whoever it's shared with. legacy falls back to
// execCommand where navigator.clipboard is missing — plain http on a LAN IP,
// which is how dev:mobile reaches a phone. `copied` resets itself after 1.5s,
// which is what swaps the icon back.
const { copy, copied, isSupported } = useClipboard({ legacy: true })
</script>

<template>
  <!-- Save, the common one, takes the outer edge. -->
  <div class="flex items-center gap-xs">
    <IconButton
      :icon="saved ? 'i-ph-bookmark-simple-fill' : 'i-ph-bookmark-simple-bold'"
      :aria-label="saved ? 'Unsave' : 'Save'"
      :aria-pressed="saved"
      @click="$emit('toggleSave')"
    />
    <IconButton
      icon="i-ph-arrow-square-out-bold"
      :to="post?.post_url"
      target="_blank"
      aria-label="Open source"
    />
    <IconButton
      v-if="isSupported"
      :icon="copied ? 'i-ph-check-bold' : 'i-ph-link-bold'"
      :aria-label="copied ? 'Link copied' : 'Copy link'"
      @click="props.post && copy(props.post.post_url)"
    />
  </div>
</template>
