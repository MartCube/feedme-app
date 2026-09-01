import type { Settings } from '~/assets/types'

// The three synced values take their unions from the API schema, so a value
// the backend would 422 can't be assigned here in the first place.
export type ThemeName = Settings['theme']

export const themes: { name: ThemeName, label: string }[] = [
  { name: 'ink', label: 'Ink' },
  { name: 'claude', label: 'Claude' },
]

export type FeedListStyle = Settings['feed_list_style']

export const feedListStyles: { name: FeedListStyle, label: string }[] = [
  { name: 'list', label: 'List' },
  { name: 'cards', label: 'Cards' },
]

// Desktop scrollbar treatment (assets/css/scrollbars.css). `auto` writes no
// rules — it's the native baseline to compare the variants against.
export type ScrollbarStyle = Settings['scrollbar_style']

export const scrollbarStyles: { name: ScrollbarStyle, label: string }[] = [
  { name: 'thin', label: 'Thin' },
  { name: 'comfortable', label: 'Comfortable' },
  { name: 'auto', label: 'System' },
]

// App-wide user preferences. These live on the account (GET/PUT /settings) so
// they follow the user across devices; the cookie persistence stays as a local
// cache, which is what renders the chosen theme server-side without a flash
// while /settings is still in flight.
export const useSettingsStore = defineStore('settings', () => {
  // See the same line in stores/feeds.ts: actions run past await boundaries,
  // where useNuxtApp() no longer has a context to find.
  const nuxtApp = useNuxtApp()

  const theme = ref<ThemeName>('ink')
  const feedListStyle = ref<FeedListStyle>('list')
  const scrollbarStyle = ref<ScrollbarStyle>('thin')

  // Desktop sidebar's Settings dropdown, persisted like the rest so the
  // sidebar reopens the way it was left. Deliberately NOT synced: it's a panel
  // affordance, not a preference worth carrying to another device.
  const sidebarSettingsOpen = ref(true)

  const payload = computed<Settings>(() => ({
    theme: theme.value,
    feed_list_style: feedListStyle.value,
    scrollbar_style: scrollbarStyle.value,
  }))

  const loaded = ref(false)
  let inflight: Promise<void> | null = null
  // What the server last told us, or what we last told it. The watcher below
  // compares against it so applying a GET doesn't echo straight back as a PUT.
  let synced: Settings | null = null

  function load() {
    if (loaded.value) return Promise.resolve()
    inflight ||= fetchSettings()
    return inflight
  }

  async function fetchSettings() {
    try {
      const remote = await nuxtApp.$api<Settings>('/settings')
      theme.value = remote.theme
      feedListStyle.value = remote.feed_list_style
      scrollbarStyle.value = remote.scrollbar_style
      synced = remote
      loaded.value = true
    }
    catch {
      // Swallowed like the home load: the persisted cookie values are a
      // perfectly good fallback. Nothing syncs while `loaded` is false, so an
      // unreachable server can't be overwritten by a local change either.
    }
    finally {
      inflight = null
    }
  }

  // A full replace, true to the verb — the store holds all three values, so
  // there's never a partial payload to send.
  watch(payload, (next) => {
    if (!loaded.value || same(next, synced)) return
    synced = next
    nuxtApp.$api('/settings', { method: 'PUT', body: next })
      // Dropping the snapshot is what makes the next change retry rather than
      // compare equal to a value the server never accepted.
      .catch(() => { synced = null })
  })

  function reset() {
    loaded.value = false
    synced = null
  }

  function same(a: Settings, b: Settings | null) {
    return Boolean(b) && (Object.keys(a) as (keyof Settings)[]).every(key => a[key] === b![key])
  }

  return { theme, feedListStyle, scrollbarStyle, sidebarSettingsOpen, loaded, load, reset }
}, {
  // The values only — never `loaded`. Restoring that from the cookie would skip
  // the GET on the next load and let the sync watcher fire against an empty
  // snapshot, turning every page load into a PUT.
  persist: { pick: ['theme', 'feedListStyle', 'scrollbarStyle', 'sidebarSettingsOpen'] },
})
