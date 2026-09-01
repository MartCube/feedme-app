// The app is login-only — there is no anonymous surface (backend.md § API), so
// the guard is global and /login is the one exception.
//
// A pure guard, deliberately: it does no fetching. The token is cookie-backed,
// so the server already knows whether there is one and can redirect before
// painting the app, but the account's data is loaded after hydration (app.vue)
// — populating the stores before the client's first render would make it
// disagree with the server's, which rendered on an empty store.
export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()

  if (to.path === '/login') {
    return auth.signedIn ? navigateTo('/') : undefined
  }

  if (!auth.signedIn) return navigateTo('/login')
})
