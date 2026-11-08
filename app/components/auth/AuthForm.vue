<script setup lang="ts">
import type { Ref } from 'vue'

// The sign-in block both signed-out screens share: Apple, Google's own
// button, an "or" hairline, email + password, and the submit. `mode` is the only thing
// that differs — which endpoint the fields go to and which autocomplete hint
// the password carries. Footer copy (the link to the other screen, the terms
// line) comes in through the slot.
//
// Built to be recognised as a login form, so the browser offers to save the
// password and autofills it next time: a real <form>, named fields,
// autocomplete="username" + current-password / new-password, and a page
// change on success — which is what tells the password manager it worked.
const props = defineProps<{
  mode: 'login' | 'signup'
  heading: string
  submitLabel: string
}>()

const auth = useAuthStore()
// Empty is a supported state: no client id, no Google button (nuxt.config.ts).
const clientId = useRuntimeConfig().public.googleClientId

const email = ref('')
const password = ref('')
const pending = ref(false)
// One message per control. A failure reported under the other one reads as
// nothing having happened — the same rule T7 settled for a refused subscribe.
const appleError = ref('')
const googleError = ref('')
const emailError = ref('')

// The form survives switching between /login and /signup (pages/login.vue),
// and what was typed should too — but not a message about the other screen.
watch(() => props.mode, () => {
  appleError.value = ''
  googleError.value = ''
  emailError.value = ''
})

async function attempt(signIn: () => Promise<void>, target: Ref<string>, failure: (error: unknown) => string) {
  if (pending.value) return
  pending.value = true
  appleError.value = ''
  googleError.value = ''
  emailError.value = ''
  try {
    await signIn()
    await navigateTo('/')
  }
  catch (error) {
    // The only place a refused sign-in is ever reported: it dies at /auth/*
    // or at the /me the store proves the token against, and neither reaches a
    // screen behind this one.
    target.value = failure(error)
  }
  finally {
    pending.value = false
  }
}

// The API's own sentence when it sent one (a taken email, a weak password,
// "Email or password is wrong"); a generic line when the request never got an
// answer at all.
function detail(error: unknown) {
  const message = (error as { data?: { detail?: unknown } }).data?.detail
  return typeof message === 'string' ? message : 'Couldn\'t reach FeedMe. Try again.'
}

function submit() {
  return attempt(
    () => props.mode === 'login'
      ? auth.signInWithEmail(email.value, password.value)
      : auth.signUp(email.value, password.value),
    emailError,
    detail,
  )
}

// Rendered ahead of the integration so the screen is the finished one; until
// Sign in with Apple is wired (backend-roadmap.md), pressing it says so rather
// than doing nothing.
function signInWithApple() {
  googleError.value = ''
  emailError.value = ''
  appleError.value = 'Sign in with Apple isn\u2019t available yet.'
}

function signInWithGoogle(response: GoogleCredentialResponse) {
  return attempt(
    () => auth.signInWithGoogle(response.credential),
    googleError,
    () => 'Google couldn\'t sign you in. Try again.',
  )
}

const googleButton = useTemplateRef<HTMLElement>('googleButton')

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
    // the wrapper clips it). The white `outline` button is also what the design
    // asks for, so the two agree.
    theme: 'outline',
    size: 'large',
    // Shape has no visible effect: the white iframe background fills the corners.
    shape: 'rectangular',
    // One wording for both modes: the button is rendered once and survives
    // switching between /login and /signup, and re-rendering it to change the
    // text would reload Google's iframe in front of the user.
    text: 'continue_with',
    // Google caps this at 400. Matching the container puts the button on the
    // same edges as the fields below it.
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
  // Signing out and coming back remounts this, and removing a script tag
  // doesn't undo what it defined — a second visit only has to re-render.
  if (window.google) renderGoogleButton()
  else load()
})

// The fields' shape, shared: the control height, the muted well, the card
// radius. Focus keeps the app's single primary line (app.config.ts).
const field = { base: 'h-12 px-sm text-body rounded-2xl bg-muted ring-default placeholder:text-dimmed' }
</script>

<template>
  <form
    method="post"
    class="flex flex-col gap-sm"
    @submit.prevent="submit"
  >
    <h2 class="text-subtitle">
      {{ heading }}
    </h2>

    <!-- Apple, then Google, stacked full width: Google's rendered button has a
         200px minimum, so the mockup's side-by-side pair doesn't fit a phone.
         Apple's button is white with black ink because Apple's guidelines
         require one of its three styles (white, black, white-outlined), not a
         theme colour; the white one matches Google's beside it. 40px tall, the
         height of Google's large button. -->
    <div class="flex flex-col gap-xs">
      <button
        type="button"
        class="flex h-10 w-full items-center justify-center gap-xs rounded-2xl bg-white text-body text-black"
        @click="signInWithApple"
      >
        <UIcon
          name="i-ph-apple-logo-fill"
          class="size-5 shrink-0"
        />
        {{ mode === 'login' ? 'Sign in with Apple' : 'Sign up with Apple' }}
      </button>
      <p
        v-if="appleError"
        class="text-caption text-error text-inset"
      >
        {{ appleError }}
      </p>
    </div>

    <div
      v-if="clientId"
      class="flex flex-col gap-xs"
    >
      <!-- Google owns the chrome inside its button. overflow-hidden trims the
           iframe's 10px bleed; rounded-2xl gives it the fields' corners. h-10
           is its large size, reserved before the script arrives so the form
           below never jumps when the button appears. -->
      <div
        ref="googleButton"
        class="h-10 overflow-hidden rounded-2xl"
      />
      <p
        v-if="googleError"
        class="text-caption text-error text-inset"
      >
        {{ googleError }}
      </p>
    </div>

    <!-- Two hairlines and the word: a divider is allowed where spacing alone
         wouldn't say "either this or that" (design-system.md § Separation). -->
    <div class="flex items-center gap-sm text-caption text-muted">
      <span class="flex-1 border-t border-default" />
      or
      <span class="flex-1 border-t border-default" />
    </div>

    <label class="flex flex-col">
      <span class="sr-only">Email</span>
      <UInput
        v-model="email"
        type="email"
        name="email"
        autocomplete="username"
        placeholder="Email"
        required
        class="w-full"
        :ui="field"
      />
    </label>
    <label class="flex flex-col">
      <span class="sr-only">Password</span>
      <UInput
        v-model="password"
        type="password"
        name="password"
        :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
        placeholder="Password"
        required
        :minlength="mode === 'signup' ? 8 : undefined"
        class="w-full"
        :ui="field"
      />
    </label>
    <!-- Invisible rather than absent at sign-up, so switching modes moves
         nothing (the same rule as the footers in pages/login.vue). -->
    <NuxtLink
      to="/reset-password"
      class="self-end text-caption font-semibold text-primary transition-colors hover-darken"
      :class="mode === 'login' ? '' : 'invisible'"
      :tabindex="mode === 'login' ? undefined : -1"
    >
      Forgot password?
    </NuxtLink>

    <BlockButton
      type="submit"
      variant="filled"
      :label="submitLabel"
    />
    <p
      v-if="emailError"
      class="text-caption text-error text-inset"
      role="alert"
    >
      {{ emailError }}
    </p>

    <slot />
  </form>
</template>
