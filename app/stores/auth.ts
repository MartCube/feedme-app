import type { Me, TokenResponse } from '~/assets/types'

// The bearer token IS the session (backend.md § Auth): opaque, hashed
// server-side, revocable instantly, sliding 30-day expiry. Persisted in a
// cookie like the settings store so a reload doesn't sign you out — but
// nothing reads it during SSR; every API call runs in the browser
// (plugins/api.ts).
export const useAuthStore = defineStore('auth', () => {
  // See the same line in stores/feeds.ts.
  const nuxtApp = useNuxtApp()

  const token = ref<string | null>(null)
  const me = ref<Me | null>(null)

  const signedIn = computed(() => Boolean(token.value))

  // Set the token, then prove it: a mistyped dev token has to fail on the
  // login screen, not as a redirect loop on the next page. Throws so the form
  // can say so. Both ways in end here — Google's only extra step is trading a
  // credential for one of these tokens first.
  async function signInWithToken(candidate: string) {
    const value = candidate.trim()
    if (!value) return
    token.value = value
    try {
      me.value = await nuxtApp.$api<Me>('/me')
    }
    catch (error) {
      clear()
      throw error
    }
    // The app booted signed-out, so nothing has loaded this account's data.
    // runWithContext because we're past an await: the stores loadAccount()
    // reaches for are resolved through the Nuxt instance this restores.
    await nuxtApp.runWithContext(loadAccount)
  }

  // Google's button hands us an id_token; the API verifies it and answers with
  // one of our own. It answers with the token alone precisely so this can hand
  // over to the path above instead of being a second one.
  async function signInWithGoogle(credential: string) {
    const { token: issued } = await nuxtApp.$api<TokenResponse>('/auth/google', {
      method: 'POST',
      body: { credential },
    })
    await signInWithToken(issued)
  }

  // Settings → Account renders this; a deep-load straight into /settings/account
  // has a token but no profile yet.
  async function loadMe() {
    if (me.value || !token.value) return
    me.value = await nuxtApp.$api<Me>('/me')
  }

  async function signOut() {
    // Deleting the row is the revocation, which is the whole reason for opaque
    // tokens over JWT. An already-dead token must not trap the user in the app,
    // so a failure here still signs out locally.
    await nuxtApp.$api('/auth/logout', { method: 'POST' }).catch(() => {})
    await nuxtApp.runWithContext(() => {
      clear()
      return navigateTo('/login')
    })
  }

  // Both exits from a session run through here: an explicit sign-out and the
  // 401 handler in plugins/api.ts. It has to leave no trace of the account —
  // the feeds store's `loaded` flag would otherwise show the next person who
  // signs in the previous one's home screen.
  function clear() {
    token.value = null
    me.value = null
    useFeedsStore().reset()
    useSettingsStore().reset()
  }

  return { token, me, signedIn, signInWithToken, signInWithGoogle, loadMe, signOut, clear }
}, {
  // Only the token: the profile is a cheap read that should never be served
  // stale from a cookie.
  persist: { pick: ['token'] },
})
