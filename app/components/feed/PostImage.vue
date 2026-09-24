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

// Measured on a bare Image of the same URL, not on the img itself: a srcset
// image's naturalWidth is divided by the density its chosen candidate claims
// (the `w` over the slot width), and the claim overstates a small source —
// fill-down hands a 480px poster back at 480 whatever width was asked for. On
// a 3x phone the 1440w candidate wins and that poster reads as 130, so every
// card would collapse. With no srcset the probe reports real pixels, and the
// file is already in memory, so it costs no second download.
function measure(event: Event) {
  const img = event.target as HTMLImageElement
  const src = img.currentSrc
  const probe = new Image()
  probe.onload = () => {
    // The desktop pane swaps posts inside this instance; a probe that lands
    // after the swap measured the previous post's image.
    if (img.currentSrc === src) hidden.value = probe.naturalWidth < MIN_WIDTH
  }
  probe.src = src
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
