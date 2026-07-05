import { autoAnimatePlugin } from '@formkit/auto-animate/vue'

export default defineNuxtPlugin((nuxtApp) => {
  if (import.meta.server) {
    // stub so SSR can render v-auto-animate; the real directive only works in the browser
    nuxtApp.vueApp.directive('auto-animate', { getSSRProps: () => ({}) })
  }
  else {
    nuxtApp.vueApp.use(autoAnimatePlugin)
  }
})
