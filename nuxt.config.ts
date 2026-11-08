export default defineNuxtConfig({
  modules: ['@nuxt/eslint', '@nuxt/ui', '@pinia/nuxt', 'pinia-plugin-persistedstate/nuxt', '@vueuse/motion/nuxt', '@vueuse/nuxt'],
  // ui/ components register unprefixed (<IconButton>); everything else keeps
  // Nuxt's folder-prefix naming (settings/Drawer.vue → <SettingsDrawer>).
  components: [
    { path: '~/components/ui', pathPrefix: false },
    '~/components',
  ],
  devtools: { enabled: true },
  app: {
    head: {
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
    },
  },
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
  // The Django API. Client-only: every call runs in the browser (the bearer
  // token never reaches the Nuxt server), which is also how the planned
  // Capacitor build behaves. Override with NUXT_PUBLIC_API_BASE.
  runtimeConfig: {
    public: {
      apiBase: 'http://localhost:8000/api/v1',
      // The Google Cloud web client the sign-in button is configured with, from
      // NUXT_PUBLIC_GOOGLE_CLIENT_ID. Empty is a supported state: /login renders
      // no Google button without it and the dev-token field still signs you in.
      googleClientId: '',
      // Where Terms and Privacy tell people to write, from NUXT_PUBLIC_CONTACT_EMAIL
      // (docs/beta-launch.md). Empty renders the pages without the contact line.
      contactEmail: '',
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
        // The delete-account confirm, one level under Account so the panel slide
        // reads it as a push. Its own record because the param above is a single
        // segment — and a record, not an alias, for the same duplicate-drop reason.
        pages.push({
          name: 'settings-delete-account',
          path: '/settings/account/delete',
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
      // /signup is the login page in its other mode, not a page of its own:
      // one component under one key, so switching between the two only swaps
      // copy. As two pages, every switch remounted the screen — the drift
      // restarted and Google's button reloaded, and the form jumped.
      const login = pages.find(page => page.path === '/login')
      if (login) {
        pages.push({
          name: 'signup',
          path: '/signup',
          file: login.file,
          meta: { key: 'auth', layout: false },
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
  // Persisted stores (the auth token, the local-only settings) live in
  // cookies, and a cookie with no maxAge is a session cookie: closing the
  // browser dropped the sign-in and every local preference. A year, renewed
  // on each write.
  piniaPluginPersistedstate: {
    cookieOptions: {
      maxAge: 60 * 60 * 24 * 365,
      sameSite: 'lax',
    },
  },
})
