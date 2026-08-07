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

// Desktop scrollbar treatment (assets/css/scrollbars.css). `auto` writes no
// rules — it's the native baseline to compare the variants against.
export type ScrollbarStyle = 'thin' | 'comfortable' | 'auto'

export const scrollbarStyles: { name: ScrollbarStyle, label: string }[] = [
  { name: 'thin', label: 'Thin' },
  { name: 'comfortable', label: 'Comfortable' },
  { name: 'auto', label: 'System' },
]

// App-wide user preferences, persisted to a cookie (plugin's Nuxt default,
// so SSR renders the chosen theme without a flash). Future appearance
// settings (font size, card style, layout) belong here too.
export const useSettingsStore = defineStore('settings', () => {
  const theme = ref<ThemeName>('ink')
  const feedListStyle = ref<FeedListStyle>('list')
  const scrollbarStyle = ref<ScrollbarStyle>('thin')

  // Desktop sidebar's Settings dropdown, persisted like the rest so the
  // sidebar reopens the way it was left. (The feed list above it is always
  // expanded — it's the sidebar's reason to exist.)
  const sidebarSettingsOpen = ref(true)

  return { theme, feedListStyle, scrollbarStyle, sidebarSettingsOpen }
}, {
  persist: true,
})
