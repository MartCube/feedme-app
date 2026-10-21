import type { Feed } from '~/assets/types'

// Display title for a feed-page uid. Resolution order per the spec:
// all → saved → feed.
export function feedTitle(uid: string, feeds: Feed[]): string {
  if (uid === 'all') return 'Home'
  if (uid === 'saved') return 'Saved'
  return feeds.find(feed => feed.uid === uid)?.name
    ?? 'Feed'
}
