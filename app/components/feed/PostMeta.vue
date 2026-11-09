<script setup lang="ts">
import type { DiscoverPost, Post, PostSource } from '~/assets/types'

// A post's meta row — where it came from, then when: the source's name
// linking out to its site, a dot, the date. Shared by the post card and the
// post page so the two read the same. relative z-10 lifts the link above the
// card's stretched title link (PostCard.vue); on the post page it's inert.
// The source rides on the post itself, named the caller's way, so this needs
// no store lookup and still says where a saved post came from after its source
// has left every feed.
// A preview post (the add wizard's, never stored) carries no source, so its
// host passes the candidate being previewed as `source` — the row then reads
// exactly as a feed's. It may carry no date either, which shows as nothing
// rather than an invented one.
const props = defineProps<{ post: Post | DiscoverPost, source?: PostSource }>()

const source = computed(() => ('source' in props.post ? props.post.source : props.source ?? null))

// A channel or subreddit carries its platform's mark; a website's link is
// marked as leaving the app.
const sourceIcon = computed(() => source.value?.type === 'website'
  ? 'i-ph-arrow-square-out-bold'
  : feedTypes.find(option => option.type === source.value?.type)?.icon)
</script>

<template>
  <div
    v-if="source || post.published_at"
    class="flex min-w-0 items-center gap-2xs text-caption text-muted"
  >
    <template v-if="source">
      <a
        :href="source.site_url || undefined"
        target="_blank"
        rel="noopener noreferrer"
        class="relative z-10 flex min-w-0 items-center gap-2xs text-primary transition-colors hover-darken"
      >
        <UIcon
          :name="sourceIcon!"
          class="size-4 shrink-0"
        />
        <span class="truncate underline underline-offset-2">{{ source.name }}</span>
      </a>
      <span
        v-if="post.published_at"
        aria-hidden="true"
      >·</span>
    </template>
    <time
      v-if="post.published_at"
      :datetime="post.published_at"
      class="shrink-0"
    >{{ formatDate(post.published_at) }}</time>
  </div>
</template>
