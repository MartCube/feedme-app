import type { Feed, FeedCandidate, Home, Source } from '~/assets/types'

// Single source of truth for the home screen: the account's feeds — each a
// named group of sources — loaded in one round-trip from GET /home. Posts are
// not here; they page in through usePostList(uid), which is what the
// polymorphic feed uid means.
export const useFeedsStore = defineStore('feeds', () => {
  // Captured here, not inside the actions: an action can be called after an
  // await (signing in loads the account once /me comes back), and by then the
  // Nuxt context useNuxtApp() needs is gone. The object is the same one the
  // api plugin adds $api to, so reading it at call time still works.
  const nuxtApp = useNuxtApp()

  const feeds = ref<Feed[]>([])

  // Gates the home render: without it the first paint flashes the "nothing
  // followed yet" empty state before /home answers.
  const loaded = ref(false)
  // The load failed and the app has nothing to show — the home empty state
  // says so instead of claiming the account follows nothing.
  const unreachable = ref(false)
  let inflight: Promise<void> | null = null

  // Called on app mount and again on sign-in, so it has to collapse into one
  // request — and stay retryable if it failed (the empty state's Try again).
  function load() {
    return loaded.value ? Promise.resolve() : reload()
  }

  function reload() {
    inflight ||= fetchHome()
    return inflight
  }

  async function fetchHome() {
    try {
      const home = await nuxtApp.$api<Home>('/home')
      // Already in display order — the server sorts by the one order column.
      feeds.value = home.feeds
      loaded.value = true
      unreachable.value = false
    }
    catch {
      // Swallowed on purpose: an API that isn't up should leave the app on its
      // feet with a line saying so, not throw out of the caller. `loaded` stays
      // false, so Try again — or the next sign-in — retries.
      unreachable.value = true
    }
    finally {
      inflight = null
    }
  }

  // First-run: nothing followed yet.
  const hasFeeds = computed(() => feeds.value.length > 0)

  // Bumped when a write that changes which posts a feed holds has *landed* —
  // a source switched on or off, added, relinked or removed, a feed created or
  // deleted. The post lists key on it to reload. Not on the optimistic change:
  // a list refetched before the server has the write reads the old posts.
  const postsRevision = ref(0)

  // Desktop master–detail selection: the feed whose post list the reader
  // shows and the open post. Synced from reader routes by the desktop shell;
  // frozen while a content page (/settings, /add) is open so returning
  // restores the reading view exactly. Mobile ignores these.
  const readerFeedUid = ref('all')
  const readerPostUid = ref<string | null>(null)
  // The active search, mirrored here for the same reason as the two above: the
  // live route says /settings while the overlay is open, so reading the query
  // off it would drop the search the moment Settings opened.
  const readerQuery = ref('')
  // Which feed-page view the post pane shows when no post is open: the tail of
  // /feed/:uid/info/… (utils/feed-info.ts), or null off those routes — then
  // the pane shows the feed page itself.
  const readerInfo = ref<string[] | null>(null)

  const readerPath = computed(() => {
    let path = `/feed/${readerFeedUid.value}`
    if (readerPostUid.value) path += `/post/${readerPostUid.value}`
    else if (readerInfo.value) path += ['/info', ...readerInfo.value].join('/')
    return readerQuery.value ? `${path}?q=${encodeURIComponent(readerQuery.value)}` : path
  })

  // Signing out has to leave nothing behind: `loaded` would otherwise keep the
  // next account looking at the previous one's feeds.
  function reset() {
    feeds.value = []
    loaded.value = false
    unreachable.value = false
    readerFeedUid.value = 'all'
    readerPostUid.value = null
    readerQuery.value = ''
    readerInfo.value = null
  }

  // Every feed write answers with the whole feed, so the store swaps one row
  // rather than patching fields — the server's view of the sources (a renamed
  // one's fallback title, a relinked one's new url) lands exactly.
  function put(feed: Feed) {
    feeds.value = feeds.value.some(f => f.uid === feed.uid)
      ? feeds.value.map(f => (f.uid === feed.uid ? feed : f))
      : [...feeds.value, feed]
  }

  // Writes are optimistic: the local change lands first and the request
  // follows, so a toggle or a rename feels instant. That leaves this helper
  // holding the other half of the deal — a failed write puts back what was on
  // screen before it, and a successful one takes the server's copy.
  async function commit(request: Promise<unknown>, rollback: () => void, changesPosts = false) {
    try {
      const answer = await request
      if (answer) put(answer as Feed)
      if (changesPosts) postsRevision.value++
    }
    catch {
      rollback()
    }
  }

  function patchLocal(uid: string, change: (feed: Feed) => Feed) {
    const previous = feeds.value
    feeds.value = feeds.value.map(feed => (feed.uid === uid ? change(feed) : feed))
    return () => {
      feeds.value = previous
    }
  }

  function patchSource(feedUid: string, sourceUid: string, change: Partial<Source>) {
    return patchLocal(feedUid, feed => ({
      ...feed,
      sources: feed.sources.map(source => (source.uid === sourceUid ? { ...source, ...change } : source)),
    }))
  }

  // The creates await instead. The backend mints every public uid and fetches
  // a new source to find out whether it's a feed at all, so there is nothing
  // honest to show before it answers — and the add wizard has somewhere to put
  // the error, which is why it escapes.

  // A new feed, optionally with its first source in the same call: a URL that
  // turns out not to be a feed then leaves no empty feed behind. Blank name /
  // description take the source's own (the backend fills them).
  async function addFeed(input: { name?: string, description?: string, candidate?: FeedCandidate }): Promise<Feed> {
    const feed = await nuxtApp.$api<Feed>('/feeds', {
      method: 'POST',
      body: {
        name: input.name?.trim() ?? '',
        description: input.description?.trim() ?? '',
        feed_url: input.candidate?.feed_url,
      },
    })
    put(feed)
    postsRevision.value++
    return feed
  }

  async function addSource(feedUid: string, candidate: FeedCandidate): Promise<Feed> {
    const feed = await nuxtApp.$api<Feed>(`/feeds/${feedUid}/sources`, {
      method: 'POST',
      body: { feed_url: candidate.feed_url },
    })
    put(feed)
    postsRevision.value++
    return feed
  }

  // Changing a source's link awaits too, for the same reason as adding one:
  // the new URL is fetched, and may not be a feed.
  async function relinkSource(feedUid: string, sourceUid: string, feedUrl: string): Promise<Feed> {
    const feed = await nuxtApp.$api<Feed>(`/feeds/${feedUid}/sources/${sourceUid}`, {
      method: 'PATCH',
      body: { feed_url: feedUrl },
    })
    put(feed)
    postsRevision.value++
    return feed
  }

  function updateFeed(uid: string, patch: { name?: string, description?: string }) {
    const body = {
      name: patch.name?.trim(),
      description: patch.description?.trim(),
    }
    if (body.name === '') return
    const rollback = patchLocal(uid, feed => ({
      ...feed,
      name: body.name ?? feed.name,
      description: body.description ?? feed.description,
    }))
    return commit(nuxtApp.$api<Feed>(`/feeds/${uid}`, { method: 'PATCH', body }), rollback)
  }

  function deleteFeed(uid: string) {
    const previous = feeds.value
    feeds.value = feeds.value.filter(feed => feed.uid !== uid)
    return commit(
      nuxtApp.$api(`/feeds/${uid}`, { method: 'DELETE' }),
      () => { feeds.value = previous },
      true,
    )
  }

  // On/off and the rename. A blank name means "the source's own title" — the
  // optimistic copy shows that straight away; the server's answer confirms it.
  function updateSource(feedUid: string, sourceUid: string, patch: { name?: string, enabled?: boolean }) {
    const local: Partial<Source> = {}
    if (patch.enabled !== undefined) local.enabled = patch.enabled
    if (patch.name !== undefined) {
      const source = feeds.value.find(f => f.uid === feedUid)?.sources.find(s => s.uid === sourceUid)
      local.name = patch.name.trim() || source?.title || ''
    }
    const rollback = patchSource(feedUid, sourceUid, local)
    return commit(
      nuxtApp.$api<Feed>(`/feeds/${feedUid}/sources/${sourceUid}`, {
        method: 'PATCH',
        body: { name: patch.name?.trim(), enabled: patch.enabled },
      }),
      rollback,
      patch.enabled !== undefined,
    )
  }

  function removeSource(feedUid: string, sourceUid: string) {
    const rollback = patchLocal(feedUid, feed => ({
      ...feed,
      sources: feed.sources.filter(source => source.uid !== sourceUid),
    }))
    return commit(
      nuxtApp.$api<Feed>(`/feeds/${feedUid}/sources/${sourceUid}`, { method: 'DELETE' }),
      rollback,
      true,
    )
  }

  return { feeds, loaded, unreachable, load, reload, reset, hasFeeds, postsRevision, readerFeedUid, readerPostUid, readerQuery, readerInfo, readerPath, addFeed, addSource, relinkSource, updateFeed, deleteFeed, updateSource, removeSource }
})
