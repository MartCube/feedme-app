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

  // Set the token, then prove it: a token that doesn't work has to fail on the
  // login screen, not as a redirect loop on the next page. Throws so the form
  // can say so. Every way in ends here — Google and email each trade what
  // they have for one of these tokens first.
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

  // Email + password: the same trade, against our own check instead of
  // Google's. Both answer with the token alone for the same reason.
  async function signInWithEmail(email: string, password: string) {
    const { token: issued } = await nuxtApp.$api<TokenResponse>('/auth/login', {
      method: 'POST',
      body: { email, password },
    })
    await signInWithToken(issued)
  }

  // Creating the account signs it in: the API answers with its first token.
  async function signUp(email: string, password: string) {
    const { token: issued } = await nuxtApp.$api<TokenResponse>('/auth/signup', {
      method: 'POST',
      body: { email, password },
    })
    await signInWithToken(issued)
  }

  // The emailed reset link carries the token; the new password signs in. Every
  // other session of the account has just ended server-side — and whatever this
  // browser was signed into may be a different account, so it goes first.
  async function resetPassword(linkToken: string, password: string) {
    const { token: issued } = await nuxtApp.$api<TokenResponse>('/auth/password/reset', {
      method: 'POST',
      body: { token: linkToken, password },
    })
    clear()
    await signInWithToken(issued)
  }

  // Always "sent", known address or not — the API answers 204 either way.
  async function requestPasswordReset(email: string) {
    await nuxtApp.$api('/auth/password/forgot', { method: 'POST', body: { email } })
  }

  // Needs no session: the link is the proof. If this browser happens to hold
  // the profile, Settings → Account should stop saying "not confirmed".
  async function confirmEmail(linkToken: string) {
    await nuxtApp.$api('/auth/email/confirm', { method: 'POST', body: { token: linkToken } })
    if (me.value) me.value = { ...me.value, email_verified: true }
  }

  async function resendConfirmation() {
    await nuxtApp.$api('/auth/email/resend', { method: 'POST' })
  }

  // Everything goes server-side in one call (DELETE /me). Unlike signOut a
  // failure must surface — the account still exists — so this throws.
  async function deleteAccount() {
    await nuxtApp.$api('/me', { method: 'DELETE' })
    await nuxtApp.runWithContext(() => {
      clear()
      return navigateTo('/login')
    })
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

  return {
    token,
    me,
    signedIn,
    signInWithGoogle,
    signInWithEmail,
    signUp,
    resetPassword,
    requestPasswordReset,
    confirmEmail,
    resendConfirmation,
    deleteAccount,
    loadMe,
    signOut,
    clear,
  }
}, {
  // Only the token: the profile is a cheap read that should never be served
  // stale from a cookie.
  persist: { pick: ['token'] },
})
