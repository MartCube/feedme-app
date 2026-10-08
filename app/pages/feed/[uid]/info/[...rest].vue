<script setup lang="ts">
// The feed page on a phone, and everything under it: edit, delete, a source's
// page, its remove confirm. One catch-all record — the tail picks the view
// (utils/feed-info.ts), and each depth is still its own path, so the reader
// flow's page slide pushes and pops between them like it does for a post.
// Captured once, not computed: the route changes before the leave slide
// finishes, and the leaving page must keep its content while animating.
const route = useRoute()
const uid = route.params.uid as string
const rest = restOf(route.params.rest)

const page = useTemplateRef('page')
const { style: swipeStyle } = useSwipeBack(page, infoBack(uid, rest))

const { feeds } = storeToRefs(useFeedsStore())
useHead({ title: computed(() => feedTitle(uid, feeds.value)) })
</script>

<template>
  <main
    ref="page"
    :style="swipeStyle"
    class="flex touch-pan-y flex-col page-inset"
  >
    <FeedInfoPanels
      :uid="uid"
      :rest="rest"
    />
  </main>
</template>
