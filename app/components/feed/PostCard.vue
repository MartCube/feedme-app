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
    class="flex flex-col gap-1 py-4"
  >
    <time
      :datetime="post.published_at"
      class="text-sm text-muted"
    >{{ formatDate(post.published_at) }}</time>
    <span class="text-xl leading-7">{{ post.title }}</span>
  </NuxtLink>
</template>
