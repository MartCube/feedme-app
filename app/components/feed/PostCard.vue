<script setup lang="ts">
import type { Post } from '~/assets/types'

defineProps<{
  post: Post
  to: string
  selected?: boolean
}>()

// Which card version the account chose. Read here rather than passed down: the
// card is the only thing that acts on it, and both hosts render this component.
const settings = useSettingsStore()
</script>

<template>
  <NuxtLink
    :to="to"
    class="-mx-sm flex flex-col gap-2xs rounded-2xl px-sm py-sm transition-colors"
    :class="selected && 'bg-elevated shadow-elevated'"
  >
    <!-- 40vw is the desktop posts pane (basis-2/5 of the shell); on mobile the
         card is the width of the screen. -->
    <FeedPostImage
      v-if="settings.postCardStyle === 'image' && post.image"
      :image="post.image"
      sizes="(min-width: 1024px) 40vw, 100vw"
    />
    <time
      :datetime="post.published_at"
      class="text-caption text-muted"
    >{{ formatDate(post.published_at) }}</time>
    <span class="text-subtitle">{{ post.title }}</span>
  </NuxtLink>
</template>
