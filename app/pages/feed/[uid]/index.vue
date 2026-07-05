<script setup lang="ts">
const { feeds, folders, posts } = storeToRefs(useFeedsStore())

// Captured once, not computed: the route params change before the leave
// slide finishes, and the leaving page must keep its content while animating.
const route = useRoute()
const uid = route.params.uid as string

const title = computed(() =>
  folders.value.find(folder => folder.uid === uid)?.name
  ?? feeds.value.find(feed => feed.uid === uid)?.name
  ?? 'Feed',
)

// Every uid shows all posts for now; the usePostList(uid) resolver (saved → folder → feed)
// comes with the data layer.
const sortedPosts = computed(() =>
  [...posts.value].sort((a, b) => b.published_at.localeCompare(a.published_at)),
)

useHead({ title })
</script>

<template>
  <main class="flex flex-col px-8 pt-8 pb-12">
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

    <h1 class="mt-8 text-title tracking-tight">
      {{ title }}
    </h1>

    <ul class="mt-2 flex flex-col">
      <li
        v-for="post in sortedPosts"
        :key="post.uid"
      >
        <FeedPostCard
          :post="post"
          :to="`/feed/${uid}/post/${post.uid}`"
        />
      </li>
    </ul>
  </main>
</template>
