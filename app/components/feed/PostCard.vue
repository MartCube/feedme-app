<script setup lang="ts">
import type { Post } from '~/assets/types'

const props = defineProps<{
  post: Post
  to: string
  selected?: boolean
}>()

// Which card version the account chose. Read here rather than passed down: the
// card is the only thing that acts on it, and both hosts render this component.
const settings = useSettingsStore()

// A few lines of the summary under the title, as text. Feeds pad it with
// their own footers, which say nothing on a card: Reddit's "submitted by /u/…
// [link] [comments]", and Hacker News's "Article URL: … Comments URL: …
// Points: … # Comments: …" — which is the whole summary there, so none shows.
const excerpt = computed(() => stripHtml(props.post.summary)
  .replace(/\s*submitted by \/u\/\S+\s*\[link\]\s*\[comments\]\s*$/, '')
  .replace(/\s*Article URL: \S+\s*Comments URL: \S+\s*Points: \d+\s*# Comments: \d+\s*$/, ''))
</script>

<template>
  <!-- Not one big link: the feed link inside it would be a link in a link. The
       title's link stretches over the whole card instead (after:inset-0), and
       the feed link sits above that layer. isolate keeps that z-10 inside the
       card, so it can't paint over the desktop pane's sticky title row.
       Two surfaces: bg-elevated at rest, bg-muted when selected or hovered
       (hover-lift, themes.css). -->
  <article
    class="relative isolate -mx-sm flex gap-sm rounded-2xl p-sm transition-colors"
    :class="selected ? 'bg-muted' : 'bg-elevated hover-lift'"
  >
    <div class="flex min-w-0 flex-1 flex-col gap-2xs">
      <FeedPostMeta :post="post" />
      <NuxtLink
        :to="to"
        class="text-subtitle after:absolute after:inset-0 after:rounded-2xl"
      >
        {{ post.title }}
      </NuxtLink>
      <!-- The image version only: compact is date and title by definition. -->
      <p
        v-if="settings.postCardStyle === 'image' && excerpt"
        class="line-clamp-3 text-body text-muted"
      >
        {{ excerpt }}
      </p>
    </div>
    <!-- A square beside the text, crowdfeed's steps: 128px on a phone, 160 /
         176 / 192 as the screen grows. The source is the 16:9 card family
         cropped to a square by object-cover, so `sizes` asks for the 16:9
         width that covers the square's height (side × 16/9). -->
    <FeedPostImage
      v-if="settings.postCardStyle === 'image' && post.image"
      :image="post.image"
      square
      sizes="(min-width: 1280px) 342px, (min-width: 1024px) 313px, (min-width: 768px) 285px, 228px"
      class="size-32 shrink-0 md:size-40 lg:size-44 xl:size-48"
    />
  </article>
</template>
