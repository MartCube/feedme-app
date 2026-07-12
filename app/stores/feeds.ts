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

  return { feeds, folders, posts, looseFeeds, memberFeeds, expandedFolderUids, isExpanded, toggleFolder, addFeed, addFolder }
})
