import { feeds as seedFeeds, folders as seedFolders, posts as seedPosts } from '~/assets/data'
import type { Feed, Folder, Post } from '~/assets/types'

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

  return { feeds, folders, posts, looseFeeds, memberFeeds, expandedFolderUids, isExpanded, toggleFolder }
})
