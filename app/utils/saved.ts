// The pinned Saved entry on the home list and its three groups. Static app
// structure (like settings-drawer.ts), NOT store folders — a Folder here would
// leak into the add-wizard destination list and the looseFeeds computed.
// Routing: /feed/saved (all saved posts) and /feed/saved_* (one group), both
// resolved by the feed page before folder/feed uids.
export interface SavedGroup {
  uid: string
  name: string
}

export const savedGroups: SavedGroup[] = [
  { uid: 'saved_bookmarks', name: 'Bookmarks' },
  { uid: 'saved_favorites', name: 'Favorites' },
  { uid: 'saved_later', name: 'Later' },
]
