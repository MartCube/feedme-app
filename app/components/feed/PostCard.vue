<script setup lang="ts">
import type { Post } from '~/assets/types'

defineProps<{
  post: Post
  to: string
}>()
</script>

<template>
  <NuxtLink
    :to="to"
    class="flex flex-col gap-2xs py-sm"
  >
    <time
      :datetime="post.published_at"
      class="text-caption text-muted"
    >{{ formatDate(post.published_at) }}</time>
    <span class="text-subtitle">{{ post.title }}</span>
  </NuxtLink>
</template>
