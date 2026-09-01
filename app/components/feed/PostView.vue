<script setup lang="ts">
import type { Post } from '~/assets/types'

// The post detail: title, time, and body for one post. Presentational — the
// host (the mobile post page, or the desktop shell's detail pane) owns the
// fetch through usePost, because the host is also what needs the title and the
// save state.
defineProps<{ post: Post | null, failed?: boolean }>()
</script>

<template>
  <div class="flex flex-col">
    <template v-if="post">
      <h1 class="mt-lg text-title tracking-tight">
        {{ post.title }}
      </h1>
      <time
        :datetime="post.published_at"
        class="mt-2xs text-caption text-muted"
      >{{ formatDate(post.published_at) }}</time>
      <!-- What RSS gave us, as text (see utils/stripHtml). The extracted
           article text is a separate field behind /posts/{uid}/article (T10). -->
      <p class="mt-md text-body">
        {{ stripHtml(post.summary) }}
      </p>
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
