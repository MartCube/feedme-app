export type ThemeName = 'ink' | 'claude'

// App-wide user preferences, persisted to localStorage. Future appearance
// settings (font size, card style, layout) belong here too.
export const useSettingsStore = defineStore('settings', () => {
  const theme = ref<ThemeName>('ink')

  return { theme }
}, {
  persist: true,
})
