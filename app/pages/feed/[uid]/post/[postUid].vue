<script setup lang="ts">
// Captured once, not computed: the route params change before the leave
// slide finishes, and the leaving page must keep its content and back link
// while animating.
const route = useRoute()
const uid = route.params.uid as string
const postUid = route.params.postUid as string

const page = useTemplateRef('page')
const { style: swipeStyle } = useSwipeBack(page, `/feed/${uid}`)

// The page owns the post: the navbar's save toggle and the document title need
// it as much as the detail view below does.
//
// Not on desktop, though: the mobile tree still renders during hydration before
// the breakpoint check flips, and the desktop shell fetches the same post a
// moment later. The synchronous check exists for exactly this (useIsDesktop's
// ref is deliberately false until mounted).
const { post, failed, saved, toggleSave } = usePost(isDesktopNow() ? null : postUid)

useHead({ title: () => post.value?.title ?? 'Post' })
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
      <IconButton
        :icon="saved ? 'i-ph-bookmark-simple-fill' : 'i-ph-bookmark-simple-bold'"
        :aria-label="saved ? 'Unsave' : 'Save'"
        :aria-pressed="saved"
        @click="toggleSave"
      />
    </Navbar>

    <FeedPostView
      :post="post"
      :failed="failed"
    />
  </main>
</template>
