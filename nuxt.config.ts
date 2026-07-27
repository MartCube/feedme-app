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
  // Nuxt UI's internal defaults are all lucide; remap every key to ph so the
  // app stays on one icon family and @iconify-json/lucide isn't needed. This
  // lives here (not app.config.ts) because Nuxt UI reads appConfig.ui.icons at
  // module setup to pick client-bundle icons — app.config.ts merges too late,
  // leaving the lucide defaults in the bundle and a dev-server warning. Miss a
  // key and its lucide default survives the merge.
  appConfig: {
    ui: {
      icons: {
        arrowDown: 'i-ph-arrow-down',
        arrowLeft: 'i-ph-arrow-left',
        arrowRight: 'i-ph-arrow-right',
        arrowUp: 'i-ph-arrow-up',
        caution: 'i-ph-warning-circle',
        check: 'i-ph-check',
        chevronDoubleLeft: 'i-ph-caret-double-left',
        chevronDoubleRight: 'i-ph-caret-double-right',
        chevronDown: 'i-ph-caret-down',
        chevronLeft: 'i-ph-caret-left',
        chevronRight: 'i-ph-caret-right',
        chevronUp: 'i-ph-caret-up',
        close: 'i-ph-x',
        copy: 'i-ph-copy',
        copyCheck: 'i-ph-checks',
        dark: 'i-ph-moon',
        drag: 'i-ph-dots-six-vertical',
        ellipsis: 'i-ph-dots-three',
        error: 'i-ph-x-circle',
        external: 'i-ph-arrow-up-right',
        eye: 'i-ph-eye',
        eyeOff: 'i-ph-eye-slash',
        file: 'i-ph-file',
        folder: 'i-ph-folder',
        folderOpen: 'i-ph-folder-open',
        hash: 'i-ph-hash',
        info: 'i-ph-info',
        light: 'i-ph-sun',
        loading: 'i-ph-circle-notch',
        menu: 'i-ph-list',
        minus: 'i-ph-minus',
        panelClose: 'i-ph-arrow-line-left',
        panelOpen: 'i-ph-arrow-line-right',
        plus: 'i-ph-plus',
        reload: 'i-ph-arrow-counter-clockwise',
        search: 'i-ph-magnifying-glass',
        stop: 'i-ph-stop',
        star: 'i-ph-star',
        success: 'i-ph-check-circle',
        system: 'i-ph-monitor',
        tip: 'i-ph-lightbulb',
        upload: 'i-ph-upload-simple',
        warning: 'i-ph-warning',
      },
    },
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
        // And for the edit-feed drawer (components/edit/Drawer.vue). One record
        // per in-drawer panel — literal `source`/`add`/`delete` segments keep
        // them unambiguous, and depth drives the panel-slide push/pop.
        // :uid is a folder_* (folder panel) or a loose feed_* (source panel).
        for (const edit of [
          { name: 'edit', path: '/edit/:uid' },
          { name: 'edit-source', path: '/edit/:uid/source/:sourceUid' },
          { name: 'edit-add', path: '/edit/:uid/add' },
          { name: 'edit-add-input', path: '/edit/:uid/add/input' },
          { name: 'edit-delete', path: '/edit/:uid/delete' },
          { name: 'edit-source-delete', path: '/edit/:uid/source/:sourceUid/delete' },
        ]) {
          pages.push({ ...edit, file: home.file, meta: { key: 'home' } })
        }
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
