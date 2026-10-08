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

// The feed the post came from, for the meta row's link. Null once the feed is
// deleted (a saved post outlives it) — then the row is the date alone.
const { feeds } = storeToRefs(useFeedsStore())
const feed = computed(() => feeds.value.find(candidate => candidate.uid === props.post.feed_uid))

// A few lines of the summary under the title, as text. Feeds pad it with
// their own footers, which say nothing on a card: Reddit's "submitted by /u/…
// [link] [comments]", and Hacker News's "Article URL: … Comments URL: …
// Points: … # Comments: …" — which is the whole summary there, so none shows.
const excerpt = computed(() => stripHtml(props.post.summary)
  .replace(/\s*submitted by \/u\/\S+\s*\[link\]\s*\[comments\]\s*$/, '')
  .replace(/\s*Article URL: \S+\s*Comments URL: \S+\s*Points: \d+\s*# Comments: \d+\s*$/, ''))

// A channel or subreddit carries its platform's mark; a website's link is
// marked as leaving the app.
const feedIcon = computed(() => feed.value?.type === 'website'
  ? 'i-ph-arrow-square-out-bold'
  : feedTypes.find(option => option.type === feed.value?.type)?.icon)
</script>

<template>
  <!-- Not one big link: the feed link inside it would be a link in a link. The
       title's link stretches over the whole card instead (after:inset-0), and
       the feed link sits above that layer. -->
  <article
    class="relative -mx-sm flex gap-sm rounded-2xl p-sm transition-colors"
    :class="selected && 'bg-elevated shadow-elevated'"
  >
    <div class="flex min-w-0 flex-1 flex-col gap-2xs">
      <div class="flex min-w-0 items-center gap-2xs text-caption text-muted">
        <a
          v-if="feed"
          :href="feed.site_url"
          target="_blank"
          rel="noopener noreferrer"
          class="relative z-10 flex min-w-0 items-center gap-2xs text-primary hover:underline"
        >
          <!-- 1px down: flex centres the icon on the capitals, but a name is
               mostly lowercase, whose middle sits ~1.2px lower at this size. -->
          <UIcon
            :name="feedIcon!"
            class="size-4 shrink-0 translate-y-px"
          />
          <span class="truncate">{{ feed.name }}</span>
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
