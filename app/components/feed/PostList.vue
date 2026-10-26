<script setup lang="ts">
// The post list (master pane): title + post cards for a feed-page uid.
// Rendered by the mobile feed page and, on desktop, by the posts pane.
// `activePostUid` is the desktop master–detail selection: the open post's
// card keeps the elevated treatment persistently.
//
// `q` is the committed search, handed in by whichever host owns the route —
// the mobile page reads it off `route.query`, the desktop shell off the store
// mirror that survives a content route. Same split as `uid`, for the same
// reason.
const props = defineProps<{
  uid: string
  q?: string
  activePostUid?: string | null
}>()

const { feeds } = storeToRefs(useFeedsStore())

const title = computed(() => feedTitle(props.uid, feeds.value))

// The Feed info button beside Search is the way into the feed page — its sources,
// their on/off, its edit. On a phone that's its own page; on desktop the feed
// page already sits in the post pane whenever no post is open, so the button
// just closes the post. Home and Saved have no page of their own, so no button.
const isDesktop = useIsDesktop()

const infoTo = computed(() => {
  if (props.uid === 'all' || props.uid.startsWith('saved')) return undefined
  return isDesktop.value ? `/feed/${props.uid}` : `/feed/${props.uid}/info`
})

// vue-router's live route, NOT Nuxt's useRoute(): this component also renders
// inside the desktop shell, which resolves no <NuxtPage/>, and Nuxt only
// re-syncs its route object when one does. useRoute() here would work on
// mobile and silently freeze on desktop.
const router = useRouter()
const route = router.currentRoute

const query = computed(() => props.q?.trim() ?? '')

// What's in the box, kept apart from what the list is paging: typing stays
// instant and the URL follows 300ms behind it.
const draft = ref(query.value)
const debounced = refDebounced(draft, 300)
const open = ref(Boolean(query.value))

// A different list is a different search.
watch(() => props.uid, () => {
  draft.value = ''
  open.value = false
})

// The query can also change from outside the box — a deep link, a reload, or
// coming back from a post — so the box follows it. Whether it did is what tells
// a navigation apart from typing: backspacing to empty empties `draft` first
// and only then the query, while a navigation drops the query with the old term
// still in the box. So the first keeps the box open to keep typing in, and the
// second closes the row back to its title.
watch(query, (value) => {
  const external = value !== draft.value.trim()
  if (external) draft.value = value
  if (value) open.value = true
  else if (external) open.value = false
})

const isReaderPath = (path: string) => path === '/' || path.startsWith('/feed/')

function commit(term: string) {
  // The debounce can outlive the route: without this, a keystroke landing just
  // after desktop Settings opened would stamp ?q= onto /settings.
  if (!isReaderPath(route.value.path)) return
  if (((route.value.query.q as string | undefined) ?? '') === term) return

  const next = { ...route.value.query }
  if (term) next.q = term
  else delete next.q
  // replace, never push — a history entry per keystroke would make Back walk
  // rout → rou → ro → r instead of leaving the page.
  router.replace({ query: next })
}

watch(debounced, value => commit(value.trim()))

function toggle() {
  if (!open.value) {
    open.value = true
    return
  }
  open.value = false
  draft.value = ''
  // Closing is immediate; waiting out the debounce would leave the results
  // filtered for a third of a second after the box is gone.
  commit('')
}

// Results carry the query in their link, so back from a post returns to them —
// and so the leaving page still sees a query while it animates out.
function postTo(postUid: string) {
  const path = `/feed/${props.uid}/post/${postUid}`
  return query.value ? `${path}?q=${encodeURIComponent(query.value)}` : path
}

// The uid resolves server-side (all → saved → saved_* → feed_*),
// so there is nothing to filter here — this list renders whatever that stream
// pages in. A query swaps the endpoint for GET /search, scoped to the same uid.
// Which posts a feed holds changes when a source is switched off, added or
// removed — the store counts those writes once they've landed, and the list
// reloads on the count. Saved lists don't depend on sources.
const { postsRevision } = storeToRefs(useFeedsStore())
const contents = computed(() => (props.uid.startsWith('saved') ? '' : String(postsRevision.value)))

const { items, pending, failed, done, loadMore } = usePostList(() => props.uid, query, contents)

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

// Desktop keys, live only while a reader route is showing — over Settings/Add
// the arrows go back to scrolling that pane. `/` opens the search and focuses
// it at once (the autofocus delay is for the phone's slide). ↓/↑ step the open
// post through the list, the first open from the feed page a push like a
// click, each step after it a replace, so Back leaves the feed rather than
// walking every post passed.
const searchBox = useTemplateRef('searchBox')

async function focusSearch() {
  open.value = true
  await nextTick()
  searchBox.value?.focus()
}

// The posts each arrow would open. defineShortcuts swallows every key it
// binds, so an arrow is bound only while it has somewhere to go: at either
// end of the list, or with no post open, it stays the pane's scroll key. Only
// the feed page opens the first post — an open post that isn't in the list (a
// deep link, a search that filtered it out) has no neighbours to step to.
const neighbours = computed(() => {
  if (!props.activePostUid) return { down: items.value[0], up: undefined }
  const at = items.value.findIndex(post => post.uid === props.activePostUid)
  if (at === -1) return { down: undefined, up: undefined }
  return { down: items.value[at + 1], up: items.value[at - 1] }
})

// A held arrow steps once: each step is a route change and a post fetch, and
// thirty a second only lag the list and then overshoot.
function step(to: { uid: string } | undefined, event: KeyboardEvent) {
  if (!to || event.repeat) return
  if (props.activePostUid) router.replace(postTo(to.uid))
  else router.push(postTo(to.uid))
}

// Enter leaves the search open with the box blurred, so Esc can no longer
// reach the box's own handler. Once there's no post above the list for the
// shell's Esc to close, it closes the search instead.
const onFeedPage = computed(() => /^\/(?:feed\/[^/]+)?$/.test(route.value.path))

defineShortcuts(computed(() => {
  if (!isDesktop.value || !isReaderPath(route.value.path)) return {}
  const { down, up } = neighbours.value
  return {
    '/': focusSearch,
    ...(down && { arrowdown: (e: KeyboardEvent) => step(down, e) }),
    ...(up && { arrowup: (e: KeyboardEvent) => step(up, e) }),
    ...(open.value && onFeedPage.value && { escape: toggle }),
  }
}))

// Enter in the live search is "done typing": it hands focus back so the arrows
// step through the results.
function blurSearch() {
  (document.activeElement as HTMLElement | null)?.blur()
}

// The posts pane follows the open post. `nearest` moves only once the card
// would leave the view, and only far enough to show it; the card's
// scroll-under-strip margin parks it below the pinned title row. The uid alone
// is watched — a page loading in must never pull the list back mid-scroll.
const list = useTemplateRef('list')
const motion = usePreferredReducedMotion()

watch(() => props.activePostUid, async (uid) => {
  if (!uid) return
  await nextTick()
  list.value?.querySelector(`[data-post-uid="${CSS.escape(uid)}"]`)?.scrollIntoView({
    block: 'nearest',
    behavior: motion.value === 'reduce' ? 'auto' : 'smooth',
  })
})
</script>

<template>
  <div class="flex flex-col">
    <!-- Fixed height so opening the box doesn't shift the list under it.
         Mobile clears its navbar with mt-lg. Desktop has no navbar here, so the
         row sits on the top-row axis with the sidebar wordmark and the post
         actions, pinned the same way (see HomeFeedList's wordmark): the pane's
         inset folds into an opaque strip so posts scroll away under it. The
         strip runs sm past the row too, so a card never scrolls flush against
         the search button; the list's top margin gives that sm back. -->
    <div class="mt-lg flex h-12 items-center gap-sm lg:sticky lg:-top-md lg:z-10 lg:-mx-lg lg:-mt-md lg:h-10 lg:box-content lg:bg-default lg:px-lg lg:pt-md lg:pb-sm">
      <h1
        v-if="!open"
        class="min-w-0 flex-1 truncate text-title tracking-tight"
      >
        {{ title }}
      </h1>
      <!-- The title's job moves into the placeholder: it names the list you're
           searching, without a noun that would be wrong for a feed or Saved.
           Escape is the X from the keyboard: it closes the box and clears the
           search. The keydown bubbles from the input to SearchInput's form,
           and stops there so the desktop shell's Esc doesn't also close the
           post. -->
      <SearchInput
        v-else
        ref="searchBox"
        v-model="draft"
        :placeholder="`Search ${title}`"
        size="md"
        autofocus
        :submit="false"
        class="min-w-0 flex-1"
        @keydown.esc.stop="toggle"
        @submit="blurSearch"
      />
      <!-- A bound pair, like the post's actions. Feed info is a real button
           rather than a glyph on the title, so it reads as pressable; it gives
           way to the search box along with the title. -->
      <div class="flex shrink-0 items-center gap-xs">
        <IconButton
          v-if="infoTo && !open"
          icon="i-ph-info-bold"
          :to="infoTo"
          aria-label="Feed info"
        />
        <IconButton
          :icon="open ? 'i-ph-x-bold' : 'i-ph-magnifying-glass-bold'"
          :aria-label="open ? 'Close search' : 'Search posts'"
          :aria-expanded="open"
          @click="toggle"
        />
      </div>
    </div>

    <ul
      ref="list"
      class="mt-md flex flex-col space-y-sm lg:mt-xs"
    >
      <li
        v-for="post in items"
        :key="post.uid"
        :data-post-uid="post.uid"
        class="lg:scroll-under-strip"
      >
        <FeedPostCard
          :post="post"
          :to="postTo(post.uid)"
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
      {{ query ? `No posts match "${query}".` : 'No posts here yet.' }}
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
