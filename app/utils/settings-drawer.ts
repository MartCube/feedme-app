import type { InjectionKey } from 'vue'

// Provided by pages/settings.vue so nested pages can close the drawer with
// its slide-down animation instead of navigating away abruptly.
export const settingsDrawerCloseKey: InjectionKey<() => void> = Symbol('settings-drawer-close')

// Single source for the settings sections: the Home list renders from it, and
// each subpage header looks up its own icon by route.
export const settingsSections = [
  { label: 'Account', icon: 'i-ph-user-bold', to: '/settings/account' },
  { label: 'Appearance', icon: 'i-ph-paint-brush-broad-bold', to: '/settings/appearance' },
  { label: 'About', icon: 'i-ph-info-bold', to: '/settings/about' },
  { label: 'Report an issue', icon: 'i-ph-bug-bold', to: '/settings/report' },
]
