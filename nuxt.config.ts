export default defineNuxtConfig({
  modules: ['@nuxt/eslint', '@nuxt/ui', '@pinia/nuxt', 'pinia-plugin-persistedstate/nuxt', '@vueuse/motion/nuxt', '@vueuse/nuxt'],
  // ui/ components register unprefixed (<IconButton>); everything else keeps
  // Nuxt's folder-prefix naming (settings/Drawer.vue → <SettingsDrawer>).
  components: [
    { path: '~/components/ui', pathPrefix: false },
    '~/components',
  ],
  devtools: { enabled: true },
  css: ['~/assets/css/main.css'],
  colorMode: {
    preference: 'dark',
    fallback: 'dark',
  },
  compatibilityDate: '2025-07-15',
  vite: {
    optimizeDeps: {
      include: [
        '@formkit/auto-animate/vue',
      ],
    },
  },
  hooks: {
    // The settings URLs render the home page component: the feed list stays
    // mounted behind the settings drawer and SettingsDrawer switches panels
    // based on route.path. One param route (not aliases — vue-router drops
    // navigation between aliases of one record as "duplicate") plus a shared
    // page key so Nuxt patches instead of remounting across the two records.
    // Nested route pages were tried twice and remount their parent page on
    // child navigation (nuxt#13094), replaying the drawer's enter animation.
    'pages:extend': function (pages) {
      const home = pages.find(page => page.path === '/')
      if (home) {
        pages.push({
          name: 'settings',
          path: '/settings/:panel?',
          file: home.file,
          meta: { key: 'home' },
        })
        // Same trick for /add: render the home component so the feed list
        // stays mounted behind the add sheet (see components/add/Drawer.vue).
        pages.push({
          name: 'add',
          path: '/add',
          file: home.file,
          meta: { key: 'home' },
        })
      }
    },
  },
  eslint: {
    config: {
      stylistic: true,
    },
  },
  // Only the two weights the type scale allows (400 body, 600 titles).
  fonts: {
    families: [
      { name: 'Sora', provider: 'google', weights: [400, 600] },
    ],
  },
})
