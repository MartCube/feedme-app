<script setup lang="ts">
// The post list (master pane): title + post cards for a feed-page uid.
// Rendered by the mobile feed page and, on desktop, by the posts pane.
// `activePostUid` is the desktop master–detail selection: the open post's
// card keeps the elevated treatment persistently.
const props = defineProps<{ uid: string, activePostUid?: string | null }>()

const { feeds, folders } = storeToRefs(useFeedsStore())

const title = computed(() => feedTitle(props.uid, feeds.value, folders.value))

// The uid resolves server-side (all → saved → saved_* → folder_* → feed_*),
// so there is nothing to filter here — this list renders whatever that stream
// pages in.
const { items, pending, failed, done, loadMore } = usePostList(() => props.uid)

// A sentinel below the list, observed against the viewport: mobile scrolls the
// page and desktop scrolls the posts pane, and neither has to be named for the
// intersection to be correct.
const sentinel = useTemplateRef<HTMLElement>('sentinel')
const atEnd = ref(false)
useIntersectionObserver(sentinel, ([entry]) => {
  atEnd.value = entry?.isIntersecting ?? false
  if (atEnd.value) loadMore()
}, { rootMargin: '400px 0px' })

// A page too short to push the sentinel out of view produces no further
// intersection event, which would stall paging — re-check once a load settles.
watch(pending, (busy) => {
  if (!busy && atEnd.value) loadMore()
})

const { selectedUid, select } = useTapSelection()
</script>

<template>
  <div class="flex flex-col">
    <h1 class="mt-lg text-title tracking-tight">
      {{ title }}
    </h1>

    <ul class="mt-md flex flex-col space-y-sm">
      <li
        v-for="post in items"
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

    <p
      v-if="failed"
      class="mt-md text-body text-muted"
    >
      Couldn't load posts.
    </p>
    <p
      v-else-if="done && !items.length"
      class="mt-md text-body text-muted"
    >
      No posts here yet.
    </p>

    <!-- Only while there's a next page: an always-present sentinel would keep
         asking for one after the list ends. -->
    <div
      v-if="!done"
      ref="sentinel"
      aria-hidden="true"
      class="h-px"
    />
  </div>
</template>
