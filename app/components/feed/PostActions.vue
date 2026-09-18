<script setup lang="ts">
import type { Post } from '~/assets/types'

// The post's two actions — Open source and Save — as one pair, because the
// mobile navbar and the desktop post pane render exactly the same buttons.
// The host owns the save state (it comes from usePost), so this only emits.
// `target` and `rel` fall through IconButton to UButton, which renders an
// absolute URL as a plain <a> and adds rel="noopener noreferrer" itself.
defineProps<{ post: Post, saved: boolean }>()
defineEmits<{ toggleSave: [] }>()
</script>

<template>
  <div class="flex items-center gap-xs">
    <IconButton
      icon="i-ph-arrow-square-out-bold"
      :to="post.post_url"
      target="_blank"
      aria-label="Open source"
    />
    <IconButton
      :icon="saved ? 'i-ph-bookmark-simple-fill' : 'i-ph-bookmark-simple-bold'"
      :aria-label="saved ? 'Unsave' : 'Save'"
      :aria-pressed="saved"
      @click="$emit('toggleSave')"
    />
  </div>
</template>
