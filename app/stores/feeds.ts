import { feeds as seedFeeds, folders as seedFolders, posts as seedPosts } from '~/assets/data'
import type { Feed, FeedCandidate, Folder, Post } from '~/assets/types'

// Where a newly added feed lands: the top-level list, or a folder by uid.
export type Destination = 'loose' | string

// Single source of truth for feed data. Seeded from the static mock for now;
// later the fetch layer fills these and components stay unchanged.
export const useFeedsStore = defineStore('feeds', () => {
  const feeds = ref<Feed[]>(seedFeeds)
  const folders = ref<Folder[]>(seedFolders)
  const posts = ref<Post[]>(seedPosts)

  const looseFeeds = computed(() =>
    feeds.value.filter(feed => !folders.value.some(folder => folder.feed_uids.includes(feed.uid))),
  )

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

  function memberFeeds(folder: Folder): Feed[] {
    return folder.feed_uids
      .map(uid => feeds.value.find(feed => feed.uid === uid))
      .filter((feed): feed is Feed => Boolean(feed))
  }

  function addFeed(candidate: FeedCandidate, destination: Destination): Feed {
    const feed: Feed = { ...candidate, uid: `feed_${crypto.randomUUID()}` }
    feeds.value = [...feeds.value, feed]

    if (destination !== 'loose') {
      // Immutable update (like feeds above) — never mutate the seed Folder in
      // place, which would leak across SSR requests via the module cache.
      folders.value = folders.value.map(folder =>
        folder.uid === destination
          ? { ...folder, feed_uids: [...folder.feed_uids, feed.uid] }
          : folder,
      )
    }

    return feed
  }

  function addFolder(name: string): Folder {
    const folder: Folder = {
      uid: `folder_${crypto.randomUUID()}`,
      name: name.trim(),
      feed_uids: [],
      muted_feed_uids: [],
    }
    folders.value = [...folders.value, folder]
    return folder
  }

  // All mutations below follow the immutable-update convention above — never
  // mutate a seed Folder/Feed in place (it leaks across SSR requests via the
  // module cache).

  function renameFolder(uid: string, name: string) {
    const trimmed = name.trim()
    if (!trimmed) return
    folders.value = folders.value.map(folder =>
      folder.uid === uid ? { ...folder, name: trimmed } : folder,
    )
  }

  // Per-folder mute: excludes a member from THIS folder's merged read only.
  function toggleMute(folderUid: string, feedUid: string) {
    folders.value = folders.value.map((folder) => {
      if (folder.uid !== folderUid) return folder
      const muted_feed_uids = folder.muted_feed_uids.includes(feedUid)
        ? folder.muted_feed_uids.filter(u => u !== feedUid)
        : [...folder.muted_feed_uids, feedUid]
      return { ...folder, muted_feed_uids }
    })
  }

  function updateFeed(uid: string, patch: Partial<Pick<Feed, 'name' | 'feed_url'>>) {
    const clean: Partial<Feed> = {}
    if (patch.name?.trim()) clean.name = patch.name.trim()
    if (patch.feed_url?.trim()) clean.feed_url = patch.feed_url.trim()
    if (!Object.keys(clean).length) return
    feeds.value = feeds.value.map(feed =>
      feed.uid === uid ? { ...feed, ...clean } : feed,
    )
  }

  // Unlinks one membership; the feed stays subscribed (goes loose if it was in
  // no other folder). Drops it from muted too.
  function removeFromFolder(folderUid: string, feedUid: string) {
    folders.value = folders.value.map(folder =>
      folder.uid === folderUid
        ? {
            ...folder,
            feed_uids: folder.feed_uids.filter(u => u !== feedUid),
            muted_feed_uids: folder.muted_feed_uids.filter(u => u !== feedUid),
          }
        : folder,
    )
  }

  // Unsubscribe everywhere: from the feeds list and from every folder.
  function deleteFeed(uid: string) {
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
  }

  return { feeds, folders, posts, looseFeeds, memberFeeds, expandedFolderUids, isExpanded, toggleFolder, addFeed, addFolder, renameFolder, toggleMute, updateFeed, removeFromFolder, deleteFeed, folderDeleteImpact, deleteFolder }
})
