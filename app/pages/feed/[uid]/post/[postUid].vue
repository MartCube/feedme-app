<script setup lang="ts">
// Captured once, not computed: the route params change before the leave
// slide finishes, and the leaving page must keep its content and back link
// while animating.
const route = useRoute()
const uid = route.params.uid as string
const postUid = route.params.postUid as string

// Captured with the params, for the same reason: back has to land on the search
// that produced this post, not on the unfiltered feed.
const q = route.query.q as string | undefined
const backTo = q ? `/feed/${uid}?q=${encodeURIComponent(q)}` : `/feed/${uid}`

const page = useTemplateRef('page')
const { style: swipeStyle } = useSwipeBack(page, backTo)

// The page owns the post: the navbar's save toggle and the document title need
// it as much as the detail view below does.
//
// Not on desktop, though: the mobile tree still renders during hydration before
// the breakpoint check flips, and the desktop shell fetches the same post a
// moment later. The synchronous check exists for exactly this (useIsDesktop's
// ref is deliberately false until mounted).
const { post, failed, article, articleState, saved, toggleSave } = usePost(isDesktopNow() ? null : postUid)

useHead({ title: () => post.value?.title ?? 'Post' })
</script>

<template>
  <main
    ref="page"
    :style="swipeStyle"
    class="flex touch-pan-y flex-col page-inset"
  >
    <!-- Actions left, Back right. No actions for a post that couldn't load:
         nothing to act on, and ml-auto holds Back right without them. -->
    <Navbar>
      <FeedPostActions
        v-if="!failed"
        :post="post"
        :saved="saved"
        @toggle-save="toggleSave"
      />
      <IconButton
        icon="i-ph-caret-left-bold"
        :to="backTo"
        aria-label="Back"
        class="ml-auto"
      />
    </Navbar>

    <FeedPostView
      :post="post"
      :failed="failed"
      :article="article"
      :article-state="articleState"
    />
  </main>
</template>
