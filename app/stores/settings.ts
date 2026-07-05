export type ThemeName = 'ink' | 'claude'

export const themes: { name: ThemeName, label: string }[] = [
  { name: 'ink', label: 'Ink' },
  { name: 'claude', label: 'Claude' },
]

// App-wide user preferences, persisted to a cookie (plugin's Nuxt default,
// so SSR renders the chosen theme without a flash). Future appearance
// settings (font size, card style, layout) belong here too.
export const useSettingsStore = defineStore('settings', () => {
  const theme = ref<ThemeName>('ink')

  return { theme }
}, {
  persist: true,
})
