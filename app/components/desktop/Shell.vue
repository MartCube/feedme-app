<script setup lang="ts">
// The ≥1024px shell: sidebar | posts pane | post pane, composed straight from
// the route + stores — NuxtPage is not rendered on desktop at all (see
// layouts/default.vue). The reading panes render from the store's reader
// selection (not the route) and stay mounted while a content page
// (/settings, /add) is open, which is what preserves feed, post, and pane
// scroll on return.
// vue-router's live route, NOT Nuxt's useRoute(): Nuxt only re-syncs its
// route object when a <NuxtPage> resolves, and the shell renders none — with
// useRoute() the URL changes but the panes never update.
const route = useRouter().currentRoute
const feedsStore = useFeedsStore()
const { feeds, hasFeeds, loaded, unreachable, readerFeedUid, readerPostUid, readerQuery, readerInfo } = storeToRefs(feedsStore)

// The posts pane carries the split; the post pane takes the rest.
const settings = useSettingsStore()
const postsPaneBasis = computed(() => ({ equal: 'basis-1/2', posts: 'basis-3/5', post: 'basis-2/5' })[settings.paneSplit])

// Sync selection from reader routes only; content routes leave it frozen.
watch(() => route.value.fullPath, () => {
  if (route.value.path === '/') {
    readerFeedUid.value = 'all'
    readerPostUid.value = null
    readerInfo.value = null
    readerQuery.value = (route.value.query.q as string | undefined) ?? ''
  }
  else if (route.value.path.startsWith('/feed/')) {
    readerFeedUid.value = route.value.params.uid as string
    readerPostUid.value = (route.value.params.postUid as string | undefined) ?? null
    readerInfo.value = /^\/feed\/[^/]+\/info(\/|$)/.test(route.value.path)
      ? restOf(route.value.params.rest)
      : null
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

// Settings and Add open in the post pane, over whatever it was showing, so the
// posts list stays in view beside them. A section or the next step replaces
// the pane, and the panels' own back buttons walk it — the same single-pane
// stack the phone has, minus the slide. /settings alone maps to the section
// list (utils/settings-panels.ts).
const settingsPanel = computed(() => settingsPanels[route.value.path])
const onAdd = computed(() => route.value.path === '/add')
const contentOpen = computed(() => onAdd.value || Boolean(settingsPanel.value))

// The mobile sheet resets the wizard when it finishes closing; here the
// equivalent moment is leaving /add by any exit (done, close, sidebar click,
// browser back).
const wizard = useAddFeedWizard()
watch(onAdd, (on, was) => {
  if (was && !on) wizard.reset()
})

// Closing returns to the frozen reading position; the reused settings panels
// close themselves via the injected key (on mobile it collapses the sheet).
function closeContent() {
  navigateTo(feedsStore.readerPath)
}
provide(settingsDrawerCloseKey, closeContent)

// Esc closes whatever is on top, one layer per press: Settings/Add back to
// the reading position, a feed-page view back the way its own back button
// goes, an open post back to its feed page. usingInput, because the add
// wizard and the feed's edit forms open with a field focused. The posts
// list's search box stops its own Esc, so there it closes only the search.
function closeTop() {
  if (contentOpen.value) return closeContent()
  const uid = readerFeedUid.value
  let to: string | undefined
  if (readerPostUid.value) to = `/feed/${uid}`
  // An empty tail is the feed page itself, which here is already the bottom.
  else if (readerInfo.value?.length) to = infoBack(uid, readerInfo.value)
  if (!to) return
  navigateTo(readerQuery.value ? `${to}?q=${encodeURIComponent(readerQuery.value)}` : to)
}

defineShortcuts({
  escape: { usingInput: true, handler: closeTop },
})

// A finished add opens the feed it landed in — the route sync above selects
// it in the sidebar.
function openLanded(feedUid: string) {
  navigateTo(`/feed/${feedUid}`)
}

useHead({
  title: () => {
    if (settingsPanel.value) return 'Settings'
    if (onAdd.value) return 'Add feed'
    return readerPost.value?.title ?? feedTitle(readerFeedUid.value, feeds.value)
  },
})
</script>

<template>
  <div class="flex h-dvh">
    <DesktopSidebar class="w-sidebar shrink-0" />

    <!-- Reading panes. Settings/Add mount over the post pane only, so the
         posts list stays beside them. -->
    <div class="flex min-w-0 flex-1">
      <!-- The split of everything right of the sidebar: 50/50, or 60/40
           toward whichever pane the account chose (Appearance). -->
      <section
        v-if="hasFeeds"
        class="shrink-0 scroll-host page-inset"
        :class="postsPaneBasis"
      >
        <FeedPostList
          :uid="readerFeedUid"
          :q="readerQuery"
          :active-post-uid="readerPostUid"
        />
      </section>
      <!-- No feeds: the empty state takes the whole area, or the posts pane's
           place while Settings/Add are open beside it. -->
      <section
        v-else-if="loaded || unreachable"
        class="flex shrink-0"
        :class="contentOpen ? postsPaneBasis : 'w-full'"
      >
        <HomeEmptyState class="h-full w-full" />
      </section>

      <!-- relative: the positioning context Settings/Add lay over. -->
      <div
        v-if="hasFeeds || contentOpen"
        class="relative min-w-0 flex-1"
      >
        <!-- Stays mounted under Settings/Add, which is what keeps the open
             post and its scroll for the way back. inert while covered, so
             Tab can't walk into what's hidden. -->
        <section
          v-if="hasFeeds"
          class="h-full scroll-host page-inset"
          :inert="contentOpen"
        >
          <template v-if="readerPostUid">
            <!-- Sits on the top-row axis with the sidebar wordmark and the posts
                 pane's title row, pinned the same way so the actions stay in
                 reach through a long read. Aligned to the actions' side within
                 the reading measure so it stays beside the text, not the pane.
                 The actions stay up from one post to the next (they wait
                 for nothing, see PostActions), so the row never blinks. The
                 strip runs sm past the row, so text never scrolls flush
                 against the buttons. -->
            <div class="sticky -top-lg z-10 -mx-lg -mt-lg bg-default px-lg pt-lg pb-sm">
              <div
                class="flex h-12 max-w-post items-center"
                :class="settings.actionSide === 'left' ? 'justify-start' : 'justify-end'"
              >
                <FeedPostActions
                  v-if="!readerPostFailed"
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
          <!-- No post open: the feed page — what this feed is, its sources and
               their on/off — or one of the views under it. Home and Saved
               have no page of their own, so they keep the prompt. -->
          <FeedInfoPanels
            v-else-if="readerFeedUid.startsWith('feed_')"
            :uid="readerFeedUid"
            :rest="readerInfo ?? []"
            class="max-w-reading"
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

        <!-- Each panel brings its own scroll-host and page-inset; this only
             covers the pane. Not capped here: a capped panel put its
             scrollbar mid-pane with dead space beyond it, so a panel holds
             its own content to a measure inside its scroll. Nothing
             animates — on desktop a step or a section just replaces the last. -->
        <section
          v-if="contentOpen"
          class="absolute inset-0 z-20 bg-default"
        >
          <AddSteps
            v-if="onAdd"
            :slide="false"
            @close="closeContent"
            @done="openLanded"
          />
          <component
            :is="settingsPanel"
            v-else
            :key="route.path"
          />
        </section>
      </div>
    </div>
  </div>
</template>
