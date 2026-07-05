import type { ThemeName } from '~/stores/settings'

export const themes: readonly { name: ThemeName, label: string }[] = [
  { name: 'ink', label: 'Ink' },
  { name: 'claude', label: 'Claude' },
]

// The only theming interface components use; the settings store stays an
// implementation detail behind it.
export function useTheme() {
  const settings = useSettingsStore()
  const { theme } = storeToRefs(settings)

  function setTheme(name: ThemeName) {
    settings.theme = name
  }

  return { theme, themes, setTheme }
}
