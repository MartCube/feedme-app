export type ThemeName = 'ink' | 'claude'

export const themes: { name: ThemeName, label: string }[] = [
  { name: 'ink', label: 'Ink' },
  { name: 'claude', label: 'Claude' },
]

export type FeedListStyle = 'list' | 'cards'

export const feedListStyles: { name: FeedListStyle, label: string }[] = [
  { name: 'list', label: 'List' },
  { name: 'cards', label: 'Cards' },
]

// App-wide user preferences, persisted to a cookie (plugin's Nuxt default,
// so SSR renders the chosen theme without a flash). Future appearance
// settings (font size, card style, layout) belong here too.
export const useSettingsStore = defineStore('settings', () => {
  const theme = ref<ThemeName>('ink')
  const feedListStyle = ref<FeedListStyle>('list')

  // Desktop sidebar's Settings dropdown, persisted like the rest so the
  // sidebar reopens the way it was left. (The feed list above it is always
  // expanded — it's the sidebar's reason to exist.)
  const sidebarSettingsOpen = ref(true)

  return { theme, feedListStyle, sidebarSettingsOpen }
}, {
  persist: true,
})
