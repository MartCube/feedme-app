import type { InjectionKey } from 'vue'

// Provided by pages/settings.vue so nested pages can close the drawer with
// its slide-down animation instead of navigating away abruptly.
export const settingsDrawerCloseKey: InjectionKey<() => void> = Symbol('settings-drawer-close')
