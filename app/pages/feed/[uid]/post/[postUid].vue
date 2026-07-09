<script setup lang="ts">
const { posts } = storeToRefs(useFeedsStore())

// Captured once, not computed: the route params change before the leave
// slide finishes, and the leaving page must keep its content and back link
// while animating.
const route = useRoute()
const { uid, postUid } = route.params
const post = computed(() => posts.value.find(p => p.uid === postUid))

useHead({ title: () => post.value?.title ?? 'Post' })
</script>

<template>
  <main class="flex flex-col px-md pt-lg pb-xl">
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

    <template v-if="post">
      <h1 class="mt-lg text-title tracking-tight">
        {{ post.title }}
      </h1>
      <time
        :datetime="post.published_at"
        class="mt-2xs text-caption text-muted"
      >{{ formatDate(post.published_at) }}</time>
      <p class="mt-md text-body">
        {{ post.content }}
      </p>
    </template>
    <p
      v-else
      class="mt-lg text-muted"
    >
      Post not found.
    </p>
  </main>
</template>
