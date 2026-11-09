<script setup lang="ts">
import type { DiscoverPost, PostSource } from '~/assets/types'

// The body of a feed preview, shared by the phone's preview step and the
// desktop posts pane: the posts as the feed's own cards show them. The
// previewed candidate stands in as every post's source, so the meta row links
// out the same way; the differences are FeedPostCard's preview mode — no Save,
// and the title opens the original. Only ever rendered with posts: an empty
// feed never opens a preview, it says so on its Preview button. No status line
// under the title — it pushed the list down against the posts pane's top-row
// axis.
defineProps<{ posts: DiscoverPost[], source: PostSource }>()
</script>

<template>
  <!-- lg:mt-xs: on desktop it sits under the pinned title row, as the posts
       list does, so swapping the two moves no card. -->
  <ul class="mt-md flex flex-col gap-sm lg:mt-xs">
    <!-- Keyed by position: a messy feed can repeat a link, and this list
         never reorders — it is replaced whole. -->
    <li
      v-for="(post, index) in posts"
      :key="index"
    >
      <FeedPostCard
        :post="post"
        :source="source"
      />
    </li>
  </ul>
</template>
