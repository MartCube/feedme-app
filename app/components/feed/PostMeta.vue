<script setup lang="ts">
import type { Post } from '~/assets/types'

// A post's meta row — where it came from, then when: the feed's name linking
// out to its site, a dot, the date. Shared by the post card and the post page
// so the two read the same. relative z-10 lifts the link above the card's
// stretched title link (PostCard.vue); on the post page it's inert.
const props = defineProps<{ post: Post }>()

// Null once the feed is deleted (a saved post outlives it) — then the row is
// the date alone.
const { feeds } = storeToRefs(useFeedsStore())
const feed = computed(() => feeds.value.find(candidate => candidate.uid === props.post.feed_uid))

// A channel or subreddit carries its platform's mark; a website's link is
// marked as leaving the app.
const feedIcon = computed(() => feed.value?.type === 'website'
  ? 'i-ph-arrow-square-out-bold'
  : feedTypes.find(option => option.type === feed.value?.type)?.icon)
</script>

<template>
  <div class="flex min-w-0 items-center gap-2xs text-caption text-muted">
    <a
      v-if="feed"
      :href="feed.site_url"
      target="_blank"
      rel="noopener noreferrer"
      class="relative z-10 flex min-w-0 items-center gap-2xs text-primary"
    >
      <UIcon
        :name="feedIcon!"
        class="size-4 shrink-0"
      />
      <span class="truncate underline underline-offset-2">{{ feed.name }}</span>
    </a>
    <span
      v-if="feed"
      aria-hidden="true"
    >·</span>
    <time
      :datetime="post.published_at"
      class="shrink-0"
    >{{ formatDate(post.published_at) }}</time>
  </div>
</template>
