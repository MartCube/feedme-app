<script setup lang="ts">
import type { PostImage } from '~/assets/types'

// The 16:9 box a post image renders in — on a card, and above the post title.
// docs/images.md § Rendering: the box is sized before the image arrives so
// nothing shifts, and anything that can't fill it removes the box rather than
// leaving a grey square or a broken-image icon behind. The attributes come
// ready from the API; the host adds the one thing only it knows, `sizes`.
const props = defineProps<{
  image: PostImage
  sizes: string
  eager?: boolean
}>()

const hidden = ref(false)

// A blown-up thumbnail reads worse than no image at all: a tracking pixel or a
// 140px Reddit thumb is hidden instead. imgproxy never enlarges, so a small
// source arrives at its own size and this is how we find out. From stage 2
// (T15d) the server knows the dimensions and answers null, and this read-time
// collapse stops happening.
const MIN_WIDTH = 320

function measure(event: Event) {
  hidden.value = (event.target as HTMLImageElement).naturalWidth < MIN_WIDTH
}

// The desktop post pane keeps one instance across posts, so a box hidden for
// one post would otherwise stay hidden for the next.
watch(() => props.image.src, () => {
  hidden.value = false
})
</script>

<template>
  <div
    v-if="!hidden"
    class="aspect-video overflow-hidden rounded-xl bg-muted"
  >
    <img
      :src="image.src"
      :srcset="image.srcset"
      :sizes="sizes"
      alt=""
      :loading="eager ? 'eager' : 'lazy'"
      :fetchpriority="eager ? 'high' : undefined"
      class="size-full object-cover"
      @load="measure"
      @error="hidden = true"
    >
  </div>
</template>
