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
const { feeds, folders, hasFeeds, loaded, unreachable, readerFeedUid, readerPostUid, readerQuery } = storeToRefs(feedsStore)

// The posts pane carries the split; the post pane takes the rest.
const settings = useSettingsStore()
const postsPaneBasis = computed(() => ({ equal: 'basis-1/2', posts: 'basis-3/5', post: 'basis-2/5' })[settings.paneSplit])

// Sync selection from reader routes only; content routes leave it frozen.
watch(() => route.value.fullPath, () => {
  if (route.value.path === '/') {
    readerFeedUid.value = 'all'
    readerPostUid.value = null
    readerQuery.value = (route.value.query.q as string | undefined) ?? ''
  }
  else if (route.value.path.startsWith('/feed/')) {
    readerFeedUid.value = route.value.params.uid as string
    readerPostUid.value = (route.value.params.postUid as string | undefined) ?? null
    readerQuery.value = (route.value.query.q as string | undefined) ?? ''
  }
}, { immediate: true })

// The shell owns the open post the way the mobile post page does, and passes
// it into the detail pane below — together with the pane's own action pair,
// since there is no navbar here to carry Save and Open source.
const {
  post: readerPost,
  failed: readerPostFailed,
  article: readerArticle,
  articleState: readerArticleState,
  saved: readerPostSaved,
  toggleSave: toggleReaderSave,
} = usePost(readerPostUid)

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

    <!-- Reading panes. The content area (settings/add/edit) mounts over these
         without unmounting them — relative is its positioning context. -->
    <div class="relative flex min-w-0 flex-1">
      <template v-if="hasFeeds">
        <!-- The split of everything right of the sidebar: 50/50, or 60/40
             toward whichever pane the account chose (Appearance). -->
        <section
          class="shrink-0 scroll-host page-inset"
          :class="postsPaneBasis"
        >
          <FeedPostList
            :uid="readerFeedUid"
            :q="readerQuery"
            :active-post-uid="readerPostUid"
          />
        </section>

        <section class="min-w-0 flex-1 scroll-host page-inset">
          <template v-if="readerPostUid">
            <!-- Sits on the top-row axis with the sidebar wordmark and the posts
                 pane's title row, pinned the same way so the actions stay in
                 reach through a long read. Right-aligned within the reading
                 measure so it stays beside the text, not the pane. Height
                 reserved (an IconButton's) so the title doesn't drop when the
                 post arrives and the actions appear. The strip runs sm past the
                 row, so text never scrolls flush against the buttons. -->
            <div class="sticky -top-lg z-10 -mx-lg -mt-lg bg-default px-lg pt-lg pb-sm">
              <div class="flex h-12 max-w-post items-center justify-end">
                <FeedPostActions
                  v-if="readerPost"
                  :post="readerPost"
                  :saved="readerPostSaved"
                  @toggle-save="toggleReaderSave"
                />
              </div>
            </div>
            <FeedPostView
              :post="readerPost"
              :failed="readerPostFailed"
              :article="readerArticle"
              :article-state="readerArticleState"
              class="max-w-post"
            />
          </template>
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
        v-else-if="loaded || unreachable"
        class="h-full w-full"
      />

      <DesktopContentOverlay />
    </div>
  </div>
</template>
