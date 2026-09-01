// The one way the app talks to the Django API. Every call goes through this
// instance so the bearer token is attached in exactly one place — and so a
// revoked token has exactly one place to be noticed.
//
// Client-only by consequence, not by config: nothing on the server ever sends a
// request through here. The route guard reads the token cookie server-side to
// decide who gets in (middleware/auth.global.ts), but the account's data is
// loaded after hydration, in the browser (app.vue).
export default defineNuxtPlugin((nuxtApp) => {
  const config = useRuntimeConfig()
  const auth = useAuthStore()

  const api = $fetch.create({
    baseURL: config.public.apiBase,
    onRequest({ options }) {
      // ofetch resolves `headers` to a real Headers instance before the hook
      // runs, so set() is the spelling — assigning an object clobbers the
      // resolved defaults.
      if (auth.token) options.headers.set('Authorization', `Bearer ${auth.token}`)
    },
    async onResponseError({ response }) {
      // The token was revoked, expired, or never valid. Opaque tokens die
      // server-side at any moment, so this is a normal event, not an error
      // path: drop the session and ask for a new one.
      if (response.status === 401) {
        // An ofetch hook runs outside the Nuxt context, which both navigateTo
        // and the stores clear() resets need.
        await nuxtApp.runWithContext(() => {
          auth.clear()
          return navigateTo('/login')
        })
      }
    },
  })

  return { provide: { api } }
})
