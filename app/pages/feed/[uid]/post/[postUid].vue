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
  <main class="flex flex-col px-8 pt-8 pb-12">
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
      <h1 class="mt-8 text-2xl font-semibold tracking-tight">
        {{ post.title }}
      </h1>
      <time
        :datetime="post.published_at"
        class="mt-1 text-sm text-muted"
      >{{ formatDate(post.published_at) }}</time>
      <p class="mt-6 text-lg leading-8">
        {{ post.content }}
      </p>
    </template>
    <p
      v-else
      class="mt-8 text-muted"
    >
      Post not found.
    </p>
  </main>
</template>
