import type { Feed } from '~/assets/types'
import { savedGroups } from './saved'

// Display title for a feed-page uid. Resolution order per the spec:
// all → saved → saved group → feed.
export function feedTitle(uid: string, feeds: Feed[]): string {
  if (uid === 'all') return 'All feeds'
  if (uid === 'saved') return 'Saved'
  return savedGroups.find(group => group.uid === uid)?.name
    ?? feeds.find(feed => feed.uid === uid)?.name
    ?? 'Feed'
}
