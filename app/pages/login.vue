<script setup lang="ts">
import type { Ref } from 'vue'

// The app is login-only (backend.md § Auth), so this is the one route the
// global middleware lets through unauthenticated.
//
// layout: false is load-bearing — layouts/default.vue renders the desktop
// shell INSTEAD of the page slot above 1024px, so a default-layout login page
// would be invisible on desktop.
definePageMeta({ layout: false })
useHead({ title: 'Sign in' })

const auth = useAuthStore()
// Empty is a supported state: no client id, no Google button, and the dev
// token is still a way in. See nuxt.config.ts.
const clientId = useRuntimeConfig().public.googleClientId

const token = ref('')
const pending = ref(false)
// One message per control. A failure reported under the other one reads as
// nothing having happened — the same rule T7 settled for a refused subscribe.
const googleError = ref('')
const tokenError = ref('')

const googleButton = useTemplateRef<HTMLElement>('googleButton')

async function attempt(signIn: () => Promise<void>, target: Ref<string>, failure: string) {
  if (pending.value) return
  pending.value = true
  googleError.value = ''
  tokenError.value = ''
  try {
    await signIn()
    await navigateTo('/')
  }
  catch {
    // The only place a refused sign-in is ever reported: a credential dies at
    // /auth/google, a pasted token at the /me the store proves it against, and
    // neither reaches a screen behind this one.
    target.value = failure
  }
  finally {
    pending.value = false
  }
}

function signInWithToken() {
  if (!token.value.trim()) return
  return attempt(
    () => auth.signInWithToken(token.value),
    tokenError,
    'That token isn\'t valid — mint a fresh one with manage.py issue_token.',
  )
}

function signInWithGoogle(response: GoogleCredentialResponse) {
  return attempt(
    () => auth.signInWithGoogle(response.credential),
    googleError,
    'Google couldn\'t sign you in. Try again.',
  )
}

function renderGoogleButton() {
  const parent = googleButton.value
  if (!parent || !window.google) return

  window.google.accounts.id.initialize({
    client_id: clientId,
    callback: signInWithGoogle,
    ux_mode: 'popup',
  })
  window.google.accounts.id.renderButton(parent, {
    // Google's iframe paints a white background behind whatever theme you pick,
    // so a dark button arrives inside a white frame (measured: the iframe bleeds
    // 10px past the requested box on every side, which no width value removes —
    // the wrapper clips it). Given that the visible block is white either way,
    // `outline` is the honest choice: filled_black clipped is a near-invisible
    // dark bar on a dark page, and it inverts the elevation direction the app
    // uses everywhere else (elevated is *lighter* — design-system.md § Themes).
    theme: 'outline',
    size: 'large',
    // Shape has no visible effect: the white iframe background fills the corners.
    shape: 'rectangular',
    text: 'continue_with',
    // Google caps this at 400. Matching the container puts the button on the
    // same edges as the header and the field below it.
    width: Math.min(parent.offsetWidth, 400),
  })
}

const { load } = useScriptTag(
  'https://accounts.google.com/gsi/client',
  renderGoogleButton,
  { manual: true },
)

onMounted(() => {
  if (!clientId) return
  // Signing out and coming back remounts this page, and removing a script tag
  // doesn't undo what it defined — a second visit only has to re-render.
  if (window.google) renderGoogleButton()
  else load()
})
</script>

<template>
  <!-- max-w-signin, not screen-sm: the column is sized to Google's 400px button
       cap (app/assets/css/layout.css), which is what keeps the two controls on
       the same edges. Never a bare max-w-md here — that name collides with the
       spacing scale. -->
  <main class="mx-auto flex min-h-dvh max-w-signin flex-col justify-center gap-lg page-inset">
    <header class="flex flex-col gap-2xs">
      <h1 class="text-title tracking-tight">
        FeedMe
      </h1>
      <p class="text-body text-muted">
        Your feeds, in one calm place. Sign in to read them.
      </p>
    </header>

    <!-- Two ways in until the dev path is retired (backend-roadmap.md T8).
         Google owns the chrome inside its button; we own the block around it,
         and the two controls are separated by spacing alone. -->
    <section class="flex flex-col gap-sm">
      <div
        v-if="clientId"
        class="flex flex-col gap-xs"
      >
        <!-- overflow-hidden trims Google's 10px iframe bleed; without it the
             button overhangs the text column on both sides. -->
        <div
          ref="googleButton"
          class="overflow-hidden"
        />
        <p
          v-if="googleError"
          class="text-caption text-error text-inset"
        >
          {{ googleError }}
        </p>
      </div>

      <div class="flex flex-col gap-xs">
        <!-- Only when Google's button is above it: with no client id the dev
             field is the only way in, and there is nothing to be "or"-ed
             against. -->
        <p
          v-if="clientId"
          class="text-caption text-muted text-inset"
        >
          Or sign in with a development token.
        </p>
        <SearchInput
          v-model="token"
          placeholder="Paste your dev token"
          submit-label="Sign in"
          paste
          autofocus
          @submit="signInWithToken"
        />
        <p
          v-if="tokenError"
          class="text-caption text-error text-inset"
        >
          {{ tokenError }}
        </p>
      </div>
    </section>
  </main>
</template>
