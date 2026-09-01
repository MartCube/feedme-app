import type { Feed, FeedCandidate, Folder, Home } from '~/assets/types'

// Where a newly added feed lands: the top-level list, or a folder by uid.
export type Destination = 'loose' | string

// Single source of truth for the home screen: the account's feeds and folders,
// loaded in one round-trip from GET /home. Posts are not here — they page in
// through usePostList(uid), which is what the polymorphic feed uid means.
export const useFeedsStore = defineStore('feeds', () => {
  // Captured here, not inside the actions: an action can be called after an
  // await (signing in loads the account once /me comes back), and by then the
  // Nuxt context useNuxtApp() needs is gone. The object is the same one the
  // api plugin adds $api to, so reading it at call time still works.
  const nuxtApp = useNuxtApp()

  const feeds = ref<Feed[]>([])
  const folders = ref<Folder[]>([])
  const savedCounts = ref<Home['saved_counts']>({ bookmarks: 0, favorites: 0, later: 0 })

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

  // Re-read even when we already have data: the cascading folder delete is the one write
  // whose failure spans both arrays, so putting it back means asking the server again.
  function reload() {
    inflight ||= fetchHome()
    return inflight
  }

  async function fetchHome() {
    try {
      const home = await nuxtApp.$api<Home>('/home')
      // `order` is the one shared 0..n-1 sequence across folders and loose
      // feeds. Applied here rather than kept around: the two lists render as
      // separate blocks today, and T7's drag-and-drop — the only thing that can
      // interleave them — re-reads /home anyway. A feed inside a folder isn't
      // in it at all (its position lives on the folder's feed_uids).
      const position = (uid: string) => {
        const index = home.order.indexOf(uid)
        return index === -1 ? Number.POSITIVE_INFINITY : index
      }
      folders.value = [...home.folders].sort((a, b) => position(a.uid) - position(b.uid))
      feeds.value = [...home.feeds].sort((a, b) => position(a.uid) - position(b.uid))
      savedCounts.value = home.saved_counts
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

  const looseFeeds = computed(() =>
    feeds.value.filter(feed => !folders.value.some(folder => folder.feed_uids.includes(feed.uid))),
  )

  // First-run: nothing followed yet (no feeds, and no folders to hold any).
  const hasFeeds = computed(() => feeds.value.length > 0 || folders.value.length > 0)

  // Feed-list UI state. Lives here (not in the page) so it survives page
  // remounts and, later, navigation to feed pages and back.
  const expandedFolderUids = ref<string[]>([])

  function isExpanded(uid: string) {
    return expandedFolderUids.value.includes(uid)
  }

  function toggleFolder(uid: string) {
    expandedFolderUids.value = isExpanded(uid)
      ? expandedFolderUids.value.filter(u => u !== uid)
      : [...expandedFolderUids.value, uid]
  }

  // Desktop master–detail selection: the feed whose post list the reader
  // shows and the open post. Synced from reader routes by the desktop shell;
  // frozen while a content page (/settings, /add, /edit/*) is open so
  // returning restores the reading view exactly. Mobile ignores these.
  const readerFeedUid = ref('all')
  const readerPostUid = ref<string | null>(null)
  const readerPath = computed(() =>
    readerPostUid.value
      ? `/feed/${readerFeedUid.value}/post/${readerPostUid.value}`
      : `/feed/${readerFeedUid.value}`,
  )

  // Signing out has to leave nothing behind: `loaded` would otherwise keep the
  // next account looking at the previous one's feeds.
  function reset() {
    feeds.value = []
    folders.value = []
    savedCounts.value = { bookmarks: 0, favorites: 0, later: 0 }
    loaded.value = false
    unreachable.value = false
    expandedFolderUids.value = []
    readerFeedUid.value = 'all'
    readerPostUid.value = null
  }

  function memberFeeds(folder: Folder): Feed[] {
    return folder.feed_uids
      .map(uid => feeds.value.find(feed => feed.uid === uid))
      .filter((feed): feed is Feed => Boolean(feed))
  }

  // Writes are optimistic: the local mutation lands first and the request follows, so Save
  // and Delete feel instant. That leaves this helper holding the other half of the deal —
  // a failed write has to put back what was on screen before it.
  async function commit(request: Promise<unknown>, rollback: () => void) {
    try {
      await request
    }
    catch {
      rollback()
    }
  }

  // The two creates are the exception: they await. The backend mints every public uid
  // (backend.md § Vocabulary), so an optimistic row would carry a uid the server is about
  // to replace — and one you could tap through to a 404 in the meantime. Both let their
  // error escape, because the add wizard has somewhere to show it.
  async function addFeed(candidate: FeedCandidate, destination: Destination): Promise<Feed> {
    const feed = await nuxtApp.$api<Feed>('/feeds', {
      method: 'POST',
      body: {
        feed_url: candidate.feed_url,
        folder_uid: destination === 'loose' ? undefined : destination,
      },
    })
    feeds.value = [...feeds.value, feed]

    if (destination !== 'loose') {
      folders.value = folders.value.map(folder =>
        folder.uid === destination
          ? { ...folder, feed_uids: [...folder.feed_uids, feed.uid] }
          : folder,
      )
    }

    return feed
  }

  async function addFolder(name: string): Promise<Folder | undefined> {
    const trimmed = name.trim()
    if (!trimmed) return
    const folder = await nuxtApp.$api<Folder>('/folders', {
      method: 'POST',
      body: { name: trimmed },
    })
    folders.value = [...folders.value, folder]
    return folder
  }

  // Every mutation below is an immutable update — replacing the array rather than mutating
  // an entry in place, which is also what makes the rollback a single assignment.

  function renameFolder(uid: string, name: string) {
    const trimmed = name.trim()
    if (!trimmed) return
    const previous = folders.value
    folders.value = folders.value.map(folder =>
      folder.uid === uid ? { ...folder, name: trimmed } : folder,
    )
    return commit(
      nuxtApp.$api(`/folders/${uid}`, { method: 'PATCH', body: { name: trimmed } }),
      () => { folders.value = previous },
    )
  }

  // Per-folder mute: the members excluded from THIS folder's merged read only.
  // Replaces the whole set — the edit panel stages toggles as a local draft and
  // commits them alongside the name when Save is pressed.
  function setMutedFeeds(folderUid: string, feedUids: string[]) {
    const previous = folders.value
    folders.value = folders.value.map(folder =>
      folder.uid === folderUid
        ? { ...folder, muted_feed_uids: [...feedUids] }
        : folder,
    )
    return commit(
      nuxtApp.$api(`/folders/${folderUid}`, {
        method: 'PATCH',
        body: { muted_feed_uids: feedUids },
      }),
      () => { folders.value = previous },
    )
  }

  // Name only. feed_url lives on the shared global Source — editing it would
  // repoint every other subscriber's feed (roadmap § Contract resolutions, 3).
  function updateFeed(uid: string, patch: Pick<Feed, 'name'>) {
    const name = patch.name.trim()
    if (!name) return
    const previous = feeds.value
    feeds.value = feeds.value.map(feed =>
      feed.uid === uid ? { ...feed, name } : feed,
    )
    return commit(
      nuxtApp.$api(`/feeds/${uid}`, { method: 'PATCH', body: { name } }),
      () => { feeds.value = previous },
    )
  }

  // Unlinks one membership; the feed stays subscribed (goes loose if it was in
  // no other folder). Drops it from muted too.
  function removeFromFolder(folderUid: string, feedUid: string) {
    const folder = folders.value.find(f => f.uid === folderUid)
    if (!folder) return
    // The membership is sent whole — PATCH replaces it, and dropping a feed drops its mute
    // with it on both sides.
    const feedUids = folder.feed_uids.filter(u => u !== feedUid)
    const previous = folders.value
    folders.value = folders.value.map(f =>
      f.uid === folderUid
        ? {
            ...f,
            feed_uids: feedUids,
            muted_feed_uids: f.muted_feed_uids.filter(u => u !== feedUid),
          }
        : f,
    )
    return commit(
      nuxtApp.$api(`/folders/${folderUid}`, { method: 'PATCH', body: { feed_uids: feedUids } }),
      () => { folders.value = previous },
    )
  }

  // Unsubscribe everywhere: from the feeds list and from every folder.
  function deleteFeed(uid: string) {
    const previousFeeds = feeds.value
    const previousFolders = folders.value
    feeds.value = feeds.value.filter(feed => feed.uid !== uid)
    folders.value = folders.value.map(folder =>
      folder.feed_uids.includes(uid)
        ? {
            ...folder,
            feed_uids: folder.feed_uids.filter(u => u !== uid),
            muted_feed_uids: folder.muted_feed_uids.filter(u => u !== uid),
          }
        : folder,
    )
    return commit(
      nuxtApp.$api(`/feeds/${uid}`, { method: 'DELETE' }),
      () => {
        feeds.value = previousFeeds
        folders.value = previousFolders
      },
    )
  }

  // Members of `uid` that belong to no other folder — deleting the folder would
  // unsubscribe exactly these. Drives the delete confirmation copy.
  function folderDeleteImpact(uid: string): number {
    const folder = folders.value.find(f => f.uid === uid)
    if (!folder) return 0
    return folder.feed_uids.filter(feedUid =>
      !folders.value.some(f => f.uid !== uid && f.feed_uids.includes(feedUid)),
    ).length
  }

  // Removes the folder and unsubscribes its members EXCEPT those also in
  // another folder (those survive as members there).
  function deleteFolder(uid: string) {
    const folder = folders.value.find(f => f.uid === uid)
    if (!folder) return
    const orphaned = folder.feed_uids.filter(feedUid =>
      !folders.value.some(f => f.uid !== uid && f.feed_uids.includes(feedUid)),
    )
    feeds.value = feeds.value.filter(feed => !orphaned.includes(feed.uid))
    folders.value = folders.value.filter(f => f.uid !== uid)
    return commit(
      nuxtApp.$api(`/folders/${uid}`, { method: 'DELETE' }),
      // The only write whose effect spans both arrays by a rule the client only mirrors —
      // putting it back means asking the server what is actually there.
      reload,
    )
  }

  return { feeds, folders, savedCounts, loaded, unreachable, load, reload, reset, looseFeeds, hasFeeds, memberFeeds, expandedFolderUids, isExpanded, toggleFolder, readerFeedUid, readerPostUid, readerPath, addFeed, addFolder, renameFolder, setMutedFeeds, updateFeed, removeFromFolder, deleteFeed, folderDeleteImpact, deleteFolder }
})
