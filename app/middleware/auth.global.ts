// The app is login-only — there is no anonymous surface (backend.md § API), so
// the guard is global and the two signed-out screens are the only exceptions.
//
// A pure guard, deliberately: it does no fetching. The token is cookie-backed,
// so the server already knows whether there is one and can redirect before
// painting the app, but the account's data is loaded after hydration (app.vue)
// — populating the stores before the client's first render would make it
// disagree with the server's, which rendered on an empty store.
const signedOutRoutes = ['/login', '/signup']

export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()

  if (signedOutRoutes.includes(to.path)) {
    return auth.signedIn ? navigateTo('/') : undefined
  }

  if (!auth.signedIn) return navigateTo('/login')
})
