<script setup lang="ts">
// The ≥1024px shell: sidebar | posts pane | post pane, composed straight from
// the route + stores — NuxtPage is not rendered on desktop at all (see
// layouts/default.vue). The reading panes render from the store's reader
// selection (not the route) and stay mounted while a content page
// (/settings, /add, /edit/*) is open, which is what preserves feed, post,
// and pane scroll on return.
// vue-router's live route, NOT Nuxt's useRoute(): Nuxt only re-syncs its
// route object when a <NuxtPage> resolves, and the shell renders none — with
// useRoute() the URL changes but the panes never update.
const route = useRouter().currentRoute
const feedsStore = useFeedsStore()
const { feeds, folders, posts, hasFeeds, readerFeedUid, readerPostUid } = storeToRefs(feedsStore)

// Sync selection from reader routes only; content routes leave it frozen.
watch(() => route.value.fullPath, () => {
  if (route.value.path === '/') {
    readerFeedUid.value = 'all'
    readerPostUid.value = null
  }
  else if (route.value.path.startsWith('/feed/')) {
    readerFeedUid.value = route.value.params.uid as string
    readerPostUid.value = (route.value.params.postUid as string | undefined) ?? null
  }
}, { immediate: true })

const readerPost = computed(() => posts.value.find(p => p.uid === readerPostUid.value))

// The reused settings/edit panels close themselves via these injected keys
// (on mobile they collapse the sheet); here closing means returning to the
// frozen reading position.
provide(settingsDrawerCloseKey, () => {
  navigateTo(feedsStore.readerPath)
})
provide(editDrawerCloseKey, () => {
  navigateTo(feedsStore.readerPath)
})

useHead({
  title: () => {
    if (route.value.path.startsWith('/settings')) return 'Settings'
    if (route.value.path === '/add') return 'Add feed'
    if (route.value.path.startsWith('/edit/')) return 'Edit'
    return readerPost.value?.title ?? feedTitle(readerFeedUid.value, feeds.value, folders.value)
  },
})
</script>

<template>
  <div class="flex h-dvh">
    <DesktopSidebar class="w-sidebar shrink-0" />

    <!-- Reading panes. The content overlay (settings/add/edit) mounts over
         these without unmounting them. -->
    <div class="relative flex min-w-0 flex-1">
      <template v-if="hasFeeds">
        <!-- 40/60 split of everything left of the sidebar. -->
        <section class="basis-2/5 shrink-0 scroll-host page-inset">
          <FeedPostList
            :uid="readerFeedUid"
            :active-post-uid="readerPostUid"
          />
        </section>

        <section class="min-w-0 basis-3/5 scroll-host page-inset">
          <FeedPostView
            v-if="readerPostUid"
            :post-uid="readerPostUid"
            class="max-w-post"
          />
          <div
            v-else
            class="flex h-full items-center justify-center"
          >
            <p class="text-body text-dimmed">
              Select a post
            </p>
          </div>
        </section>
      </template>
      <HomeEmptyState
        v-else
        class="h-full w-full"
      />

      <DesktopContentOverlay />
    </div>
  </div>
</template>
