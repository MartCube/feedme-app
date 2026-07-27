import type { InjectionKey } from 'vue'

// Provided by components/edit/Drawer.vue so its base panels (folder / loose
// source) can close the sheet with vaul's slide-down animation instead of
// navigating away abruptly — the same pattern as settingsDrawerCloseKey.
export const editDrawerCloseKey: InjectionKey<() => void> = Symbol('edit-drawer-close')
