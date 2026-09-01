import type { SavedGroupName } from '~/assets/types'

// The pinned Saved entry on the home list and its three groups. Static app
// structure (like settings-drawer.ts), NOT store folders — a Folder here would
// leak into the add-wizard destination list and the looseFeeds computed.
// Routing: /feed/saved (all saved posts) and /feed/saved_* (one group), both
// resolved by the feed page before folder/feed uids.
export interface SavedGroup {
  uid: string
  name: string
  // The key this group counts under in /home's saved_counts — the API's own
  // name for it, without the routing prefix.
  group: SavedGroupName
}

export const savedGroups: SavedGroup[] = [
  { uid: 'saved_bookmarks', name: 'Bookmarks', group: 'bookmarks' },
  { uid: 'saved_favorites', name: 'Favorites', group: 'favorites' },
  { uid: 'saved_later', name: 'Later', group: 'later' },
]
