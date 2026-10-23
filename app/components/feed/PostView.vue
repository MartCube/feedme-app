<script setup lang="ts">
import type { Post } from '~/assets/types'

// The post detail: title, time, and body for one post. Presentational — the
// host (the mobile post page, or the desktop shell's detail pane) owns the
// fetch through usePost, because the host is also what needs the title and the
// save state. The article arrives separately from the post and the body
// follows its state: a skeleton while it's in flight, the article as markup
// when there is one, the RSS summary as text when there isn't.
defineProps<{
  post: Post | null
  failed?: boolean
  article: string | null
  articleState: 'loading' | 'ok' | 'unavailable'
}>()

// The sanitiser keeps <a href> but no target, so a link inside the article
// would otherwise navigate the app away (and the planned Capacitor build has
// no tab to come back from). Delegated, so it covers every link in one place —
// and it's the hook the Capacitor Browser plugin replaces later.
function openLink(event: MouseEvent) {
  const link = (event.target as HTMLElement).closest('a[href]')
  if (!link) return
  event.preventDefault()
  window.open(link.getAttribute('href')!, '_blank', 'noopener,noreferrer')
}
</script>

<template>
  <!-- isolate, like PostCard: the meta row's source link is relative z-10
       (lifted for the card's stretched link), and without its own stacking
       context it paints over the desktop pane's sticky action strip. -->
  <div class="isolate flex flex-col">
    <template v-if="post">
      <!-- Title and meta first, then the picture: what it is and where it's
           from read before the largest thing on the screen. mt-lg clears the
           mobile navbar; on desktop the pinned action strip above already ends
           in sm of its own (desktop/Shell.vue), so xs more sits the title
           close under the actions it belongs to. -->
      <h1 class="mt-lg text-title tracking-tight lg:mt-xs">
        {{ post.title }}
      </h1>
      <FeedPostMeta
        :post="post"
        class="mt-2xs"
      />
      <!-- A video post is its video: the player takes the image's slot. -->
      <FeedPostVideo
        v-if="post.video"
        :video="post.video"
        class="mt-md"
      />
      <!-- 56rem is --container-post, the measure the pane caps the body at.
           Eager and high priority: it is the largest thing on the screen, and
           lazy loading inside a drawer has bitten this repo before.
           no-upscale: a small source sits at its own size instead of blurring
           across the pane. -->
      <FeedPostImage
        v-else-if="post.image"
        :image="post.image"
        sizes="(min-width: 1024px) 56rem, 100vw"
        eager
        no-upscale
        class="mt-md"
      />

      <div
        v-if="articleState === 'loading'"
        class="mt-md flex flex-col gap-xs"
        aria-busy="true"
      >
        <USkeleton class="h-4 w-full" />
        <USkeleton class="h-4 w-full" />
        <USkeleton class="h-4 w-2/3" />
      </div>
      <!-- The one field the app renders as markup: sanitised server-side
           against the backend's own allowlist (core/extract.py, nh3) before it
           is ever stored, so what arrives here is ours to trust. -->
      <!-- eslint-disable vue/no-v-html -->
      <div
        v-else-if="articleState === 'ok'"
        class="mt-md text-body article"
        @click="openLink"
        v-html="article"
      />
      <!-- eslint-enable vue/no-v-html -->
      <template v-else>
        <!-- What RSS gave us, as text (see utils/stripHtml) — untrusted
             third-party markup, never rendered as HTML. A video's description
             is plain text already and its line breaks are its layout, so it
             skips the stripping, which collapses them. -->
        <p
          class="mt-md text-body"
          :class="post.video && 'whitespace-pre-line'"
        >
          {{ post.video ? post.summary : stripHtml(post.summary) }}
        </p>
        <!-- The video is the post; Open source in the action bar still
             reaches YouTube. -->
        <a
          v-if="!post.video"
          :href="post.post_url"
          target="_blank"
          rel="noopener noreferrer"
          class="mt-md self-start text-body text-primary transition-colors hover-darken"
        >
          Read the full post
        </a>
      </template>
    </template>
    <!-- `failed` is any error, not only a 404 — same wording rule as the home
         screen's unreachable state: don't blame the content for the server. -->
    <p
      v-else-if="failed"
      class="mt-md text-body text-muted"
    >
      Couldn't load this post.
    </p>
  </div>
</template>
