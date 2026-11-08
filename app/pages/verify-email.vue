<script setup lang="ts">
// Where the "Confirm your email" link lands (?token=…). Confirms on arrival,
// with no session needed: the token is the proof, and the link is often opened
// in a mail app's browser rather than where the account is signed in.
// layout: false for the same reason as pages/login.vue.
definePageMeta({ layout: false })

const auth = useAuthStore()
const route = useRoute()
const linkToken = typeof route.query.token === 'string' ? route.query.token : ''

const state = ref<'confirming' | 'confirmed' | 'failed'>('confirming')
const error = ref('')

const copy = {
  confirming: { hero: ['Confirming', 'your email…'], lede: 'One moment.' },
  confirmed: { hero: ['Email', 'confirmed.'], lede: 'Thanks. Your account is all set.' },
  failed: { hero: ['That link', 'didn’t work.'], lede: 'Each link works once, for three days. Send a new one from Settings → Account.' },
} as const

useHead({ title: 'Confirm email' })

// Client-only like every API call (data-layer rules): SSR renders "Confirming".
onMounted(async () => {
  if (!linkToken) {
    state.value = 'failed'
    return
  }
  try {
    await auth.confirmEmail(linkToken)
    state.value = 'confirmed'
  }
  catch (caught) {
    // A refused link is what the lede already says; only an unreachable API
    // needs a line of its own.
    if ((caught as { statusCode?: number }).statusCode !== 400) {
      error.value = 'Couldn’t reach FeedMe. Reload to try again.'
    }
    state.value = 'failed'
  }
})
</script>

<template>
  <AuthShell
    :mode="state"
    :copy="copy"
  >
    <div
      class="flex flex-col gap-sm"
      role="status"
    >
      <p
        v-if="error"
        class="text-caption text-error text-inset"
      >
        {{ error }}
      </p>
      <BlockButton
        v-if="state !== 'confirming'"
        variant="filled"
        :label="auth.signedIn ? 'Open FeedMe' : 'Log in'"
        @click="navigateTo(auth.signedIn ? '/' : '/login')"
      />
    </div>
  </AuthShell>
</template>
