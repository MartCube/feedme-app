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
  <div class="flex flex-col">
    <template v-if="post">
      <!-- 56rem is --container-post, the measure the pane caps the body at.
           Eager and high priority: it is the largest thing on the screen, and
           lazy loading inside a drawer has bitten this repo before. -->
      <FeedPostImage
        v-if="post.image"
        :image="post.image"
        sizes="(min-width: 1024px) 56rem, 100vw"
        eager
        class="mt-lg"
      />
      <h1
        class="text-title tracking-tight"
        :class="post.image ? 'mt-md' : 'mt-lg'"
      >
        {{ post.title }}
      </h1>
      <time
        :datetime="post.published_at"
        class="mt-2xs text-caption text-muted"
      >{{ formatDate(post.published_at) }}</time>

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
             third-party markup, never rendered as HTML. -->
        <p class="mt-md text-body">
          {{ stripHtml(post.summary) }}
        </p>
        <a
          :href="post.post_url"
          target="_blank"
          rel="noopener noreferrer"
          class="mt-md self-start text-body text-primary"
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
