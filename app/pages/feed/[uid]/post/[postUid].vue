<script setup lang="ts">
const { posts } = storeToRefs(useFeedsStore())

// Captured once, not computed: the route params change before the leave
// slide finishes, and the leaving page must keep its content and back link
// while animating.
const route = useRoute()
const uid = route.params.uid as string
const postUid = route.params.postUid as string

const page = useTemplateRef('page')
const { style: swipeStyle } = useSwipeBack(page, `/feed/${uid}`)

useHead({ title: () => posts.value.find(p => p.uid === postUid)?.title ?? 'Post' })
</script>

<template>
  <main
    ref="page"
    :style="swipeStyle"
    class="flex touch-pan-y flex-col page-inset"
  >
    <Navbar>
      <IconButton
        icon="i-ph-caret-left-bold"
        :to="`/feed/${uid}`"
        aria-label="Back"
      />
      <!-- TODO: wire save once bookmarking exists. -->
      <IconButton
        icon="i-ph-bookmark-simple-bold"
        aria-label="Save"
      />
    </Navbar>

    <FeedPostView :post-uid="postUid" />
  </main>
</template>
