<script setup lang="ts">
import type { PostVideo } from '~/assets/types'

// A YouTube post's player, in the slot a post image takes on the post page —
// the same muted, rounded box, sized before anything loads. The src arrives
// ready from the API (privacy-enhanced host, inline playback on iOS); the app
// never builds it. A Short is vertical, so it gets a 9:16 box sized by the
// screen's height (video-short, assets/css/layout.css) instead of 16:9.
defineProps<{
  video: PostVideo
}>()
</script>

<template>
  <div
    class="overflow-hidden rounded-xl bg-muted"
    :class="video.vertical ? 'mx-auto video-short' : 'aspect-video'"
  >
    <!-- Keyed on the src: the desktop pane keeps one PostView across posts,
         and changing an iframe's src adds a browser history entry, so Back
         would step the old video instead of leaving the post. A new element
         doesn't. The attributes are YouTube's own embed set — the referrer
         policy is spelled out because its player refuses to start without
         one. -->
    <iframe
      :key="video.src"
      :src="video.src"
      title="YouTube video player"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
      referrerpolicy="strict-origin-when-cross-origin"
      allowfullscreen
      class="size-full"
    />
  </div>
</template>
