<script setup lang="ts">
const { feeds } = storeToRefs(useFeedsStore())

// Captured once, not computed: the route params change before the leave
// slide finishes, and the leaving page must keep its content while animating.
const route = useRoute()
const uid = route.params.uid as string

// Live while this page is the one on screen, frozen the moment it isn't. The
// route changes before the leave slide finishes — the same reason `uid` above
// is captured rather than computed — but the query has to keep updating while
// you type, so it's a tracked ref instead of a constant. Without the guard,
// tapping Feeds would blank the search results mid-slide.
const q = ref((route.query.q as string | undefined) ?? '')
watch(() => route.fullPath, () => {
  if (route.params.uid === uid && !route.params.postUid) {
    q.value = (route.query.q as string | undefined) ?? ''
  }
})

const page = useTemplateRef('page')
const { style: swipeStyle } = useSwipeBack(page, '/')

useHead({ title: computed(() => feedTitle(uid, feeds.value)) })
</script>

<template>
  <main
    ref="page"
    :style="swipeStyle"
    class="flex touch-pan-y flex-col page-inset"
  >
    <Navbar>
      <IconButton
        icon="i-ph-sidebar-simple-bold"
        to="/"
        aria-label="Feeds"
      />
      <!-- Search lives on the list's own title row (FeedPostList), which the
           desktop posts pane shares — this navbar doesn't exist there. -->
    </Navbar>

    <FeedPostList
      :uid="uid"
      :q="q"
    />
  </main>
</template>
