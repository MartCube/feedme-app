import type { Component } from 'vue'
import { SettingsAbout, SettingsAccount, SettingsAppearance, SettingsHome, SettingsReport } from '#components'

// Route → panel component map for the settings screens. Shared by the mobile
// bottom sheet (settings/Drawer.vue) and the desktop content page — panels are
// plain components switched by path, never nested NuxtPage (nuxt#13094).
export const settingsPanels: Record<string, Component> = {
  '/settings': SettingsHome,
  '/settings/about': SettingsAbout,
  '/settings/account': SettingsAccount,
  '/settings/appearance': SettingsAppearance,
  '/settings/report': SettingsReport,
}
