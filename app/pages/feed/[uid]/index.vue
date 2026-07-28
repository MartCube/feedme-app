<script setup lang="ts">
const { feeds, folders } = storeToRefs(useFeedsStore())

// Captured once, not computed: the route params change before the leave
// slide finishes, and the leaving page must keep its content while animating.
const route = useRoute()
const uid = route.params.uid as string

const page = useTemplateRef('page')
const { style: swipeStyle } = useSwipeBack(page, '/')

useHead({ title: computed(() => feedTitle(uid, feeds.value, folders.value)) })
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
      <!-- TODO: wire search (filter feed posts) once the feature exists. -->
      <IconButton
        icon="i-ph-magnifying-glass-bold"
        aria-label="Search"
      />
    </Navbar>

    <FeedPostList :uid="uid" />
  </main>
</template>
