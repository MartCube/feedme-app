<script setup lang="ts">
import type { Post } from '~/assets/types'

// A post's meta row — where it came from, then when: the source's name
// linking out to its site, a dot, the date. Shared by the post card and the
// post page so the two read the same. relative z-10 lifts the link above the
// card's stretched title link (PostCard.vue); on the post page it's inert.
// The source rides on the post itself, named the caller's way, so this needs
// no store lookup and still says where a saved post came from after its source
// has left every feed.
const props = defineProps<{ post: Post }>()

// A channel or subreddit carries its platform's mark; a website's link is
// marked as leaving the app.
const sourceIcon = computed(() => props.post.source.type === 'website'
  ? 'i-ph-arrow-square-out-bold'
  : feedTypes.find(option => option.type === props.post.source.type)?.icon)
</script>

<template>
  <div class="flex min-w-0 items-center gap-2xs text-caption text-muted">
    <a
      :href="post.source.site_url || undefined"
      target="_blank"
      rel="noopener noreferrer"
      class="relative z-10 flex min-w-0 items-center gap-2xs text-primary"
    >
      <UIcon
        :name="sourceIcon!"
        class="size-4 shrink-0"
      />
      <span class="truncate underline underline-offset-2">{{ post.source.name }}</span>
    </a>
    <span aria-hidden="true">·</span>
    <time
      :datetime="post.published_at"
      class="shrink-0"
    >{{ formatDate(post.published_at) }}</time>
  </div>
</template>
