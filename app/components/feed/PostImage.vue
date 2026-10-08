<script setup lang="ts">
import type { PostImage } from '~/assets/types'

// The box a post image renders in — 16:9 above the post title, square beside
// a card's text.
// docs/images.md § Rendering: the box is sized before the image arrives so
// nothing shifts, and anything that can't fill it removes the box rather than
// leaving a grey square or a broken-image icon behind. The attributes come
// ready from the API; the host adds the one thing only it knows, `sizes`.
const props = defineProps<{
  image: PostImage
  sizes: string
  eager?: boolean
  square?: boolean
  // Never wider than the image's own pixels. A 640px Reddit preview stretched
  // across a 1100px post pane is a blur; capped, it sits centred at its size.
  noUpscale?: boolean
}>()

const hidden = ref(false)
const naturalWidth = ref<number>()

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
    if (img.currentSrc !== src) return
    hidden.value = probe.naturalWidth < MIN_WIDTH
    naturalWidth.value = probe.naturalWidth
  }
  probe.src = src
}

// The desktop post pane keeps one instance across posts, so a box hidden for
// one post would otherwise stay hidden for the next.
watch(() => props.image.src, () => {
  hidden.value = false
  naturalWidth.value = undefined
})
</script>

<template>
  <div
    v-if="!hidden"
    class="overflow-hidden rounded-xl bg-muted"
    :class="[square ? 'aspect-square' : 'aspect-video', noUpscale && 'mx-auto w-full']"
    :style="noUpscale && naturalWidth ? { maxWidth: `${naturalWidth}px` } : undefined"
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
