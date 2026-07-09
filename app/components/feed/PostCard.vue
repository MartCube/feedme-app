<script setup lang="ts">
import type { Post } from '~/assets/types'

defineProps<{
  post: Post
  to: string
  selected?: boolean
}>()
</script>

<template>
  <NuxtLink
    :to="to"
    class="-mx-sm flex flex-col gap-2xs rounded-2xl px-sm py-sm transition-colors"
    :class="selected && 'bg-elevated shadow-elevated'"
  >
    <time
      :datetime="post.published_at"
      class="text-caption text-muted"
    >{{ formatDate(post.published_at) }}</time>
    <span class="text-subtitle">{{ post.title }}</span>
  </NuxtLink>
</template>
