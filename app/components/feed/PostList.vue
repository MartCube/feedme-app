<script setup lang="ts">
// The post list (master pane): title + post cards for a feed-page uid.
// Rendered by the mobile feed page and, on desktop, by the posts pane.
// `activePostUid` is the desktop master–detail selection: the open post's
// card keeps the elevated treatment persistently.
const props = defineProps<{ uid: string, activePostUid?: string | null }>()

const { feeds, folders, posts } = storeToRefs(useFeedsStore())

const title = computed(() => feedTitle(props.uid, feeds.value, folders.value))

// Every uid shows all posts for now — deliberate while on mock data (real
// filtering would leave a handful of posts per list and kill the feel); the
// usePostList(uid) resolver comes with the data layer.
const sortedPosts = computed(() =>
  [...posts.value].sort((a, b) => b.published_at.localeCompare(a.published_at)),
)

const { selectedUid, select } = useTapSelection()
</script>

<template>
  <div class="flex flex-col">
    <h1 class="mt-lg text-title tracking-tight">
      {{ title }}
    </h1>

    <ul class="mt-md flex flex-col space-y-sm">
      <li
        v-for="post in sortedPosts"
        :key="post.uid"
      >
        <FeedPostCard
          :post="post"
          :to="`/feed/${uid}/post/${post.uid}`"
          :selected="selectedUid === post.uid || activePostUid === post.uid"
          @pointerdown="select(post.uid)"
        />
      </li>
    </ul>
  </div>
</template>
