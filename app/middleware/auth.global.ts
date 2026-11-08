// The app is login-only — there is no anonymous surface (backend.md § API), so
// the guard is global and the signed-out screens are the only exceptions.
//
// A pure guard, deliberately: it does no fetching. The token is cookie-backed,
// so the server already knows whether there is one and can redirect before
// painting the app, but the account's data is loaded after hydration (app.vue)
// — populating the stores before the client's first render would make it
// disagree with the server's, which rendered on an empty store.
const signedOutRoutes = ['/login', '/signup']
// Open either way. The email links land on the first two, often in a mail app's
// browser with no session, or signed in as somebody else. Terms and Privacy
// have to be readable before an account exists.
const openRoutes = ['/reset-password', '/verify-email', '/terms', '/privacy']

export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()

  if (openRoutes.includes(to.path)) return

  if (signedOutRoutes.includes(to.path)) {
    return auth.signedIn ? navigateTo('/') : undefined
  }

  if (!auth.signedIn) return navigateTo('/login')
})
