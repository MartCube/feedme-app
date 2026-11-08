<script setup lang="ts">
// Both halves of "forgot password", on the login screen's frame (AuthShell).
// Without a token: ask for the address and send the link. With one (the
// emailed link, ?token=…): choose the new password, which signs you in.
//
// Open signed in or out (middleware/auth.global.ts): the link is often opened
// in a mail app's browser, or in one signed into another account.
// layout: false for the same reason as pages/login.vue.
definePageMeta({ layout: false })

const auth = useAuthStore()
const route = useRoute()
// Captured once: the page doesn't navigate between its two modes, and the
// "ask for a new link" exit is a full navigation to the bare path.
const linkToken = typeof route.query.token === 'string' ? route.query.token : ''
const mode = linkToken ? 'choose' : 'request'

const copy = {
  request: {
    hero: ['Forgot your', 'password?'],
    lede: 'Enter your email and we’ll send you a link to choose a new one.',
  },
  choose: {
    hero: ['Choose a', 'new password.'],
    lede: 'You’ll be signed in with it, and signed out everywhere else.',
  },
} as const

useHead({ title: mode === 'choose' ? 'New password' : 'Reset password' })

const email = ref('')
const password = ref('')
const pending = ref(false)
const sent = ref(false)
const error = ref('')
// A dead link can't be fixed by retyping; it needs a new one.
const linkDead = ref(false)

function detail(caught: unknown) {
  const message = (caught as { data?: { detail?: unknown } }).data?.detail
  return typeof message === 'string' ? message : 'Couldn’t reach FeedMe. Try again.'
}

async function submit() {
  if (pending.value) return
  pending.value = true
  error.value = ''
  try {
    if (mode === 'request') {
      await auth.requestPasswordReset(email.value)
      sent.value = true
    }
    else {
      await auth.resetPassword(linkToken, password.value)
      await navigateTo('/')
    }
  }
  catch (caught) {
    error.value = detail(caught)
    linkDead.value = (caught as { statusCode?: number }).statusCode === 400
  }
  finally {
    pending.value = false
  }
}

// The same field shape as AuthForm's.
const field = { base: 'h-12 px-sm text-body rounded-2xl bg-muted ring-default placeholder:text-dimmed' }
</script>

<template>
  <AuthShell
    :mode="mode"
    :copy="copy"
  >
    <div
      v-if="sent"
      class="flex flex-col gap-sm"
      role="status"
    >
      <h2 class="text-subtitle">
        Check your inbox
      </h2>
      <p class="text-body text-muted">
        If there's an account for <span class="font-semibold text-default">{{ email }}</span>,
        a link is on its way. It works for an hour.
      </p>
      <BlockButton
        label="Back to log in"
        variant="filled"
        @click="navigateTo('/login')"
      />
    </div>

    <form
      v-else
      method="post"
      class="flex flex-col gap-sm"
      @submit.prevent="submit"
    >
      <h2 class="text-subtitle">
        {{ mode === 'choose' ? 'New password' : 'Reset password' }}
      </h2>

      <label
        v-if="mode === 'request'"
        class="flex flex-col"
      >
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
      <label
        v-else
        class="flex flex-col"
      >
        <span class="sr-only">New password</span>
        <UInput
          v-model="password"
          type="password"
          name="password"
          autocomplete="new-password"
          placeholder="New password"
          required
          :minlength="8"
          class="w-full"
          :ui="field"
        />
      </label>

      <BlockButton
        type="submit"
        variant="filled"
        :disabled="pending"
        :label="mode === 'choose' ? 'Save and log in' : 'Send reset link'"
      />
      <p
        v-if="error"
        class="text-caption text-error text-inset"
        role="alert"
      >
        {{ error }}
      </p>

      <p class="text-center text-caption text-muted">
        <a
          v-if="linkDead"
          href="/reset-password"
          class="font-semibold text-primary transition-colors hover-darken"
        >Send a new link</a>
        <NuxtLink
          v-else
          to="/login"
          class="font-semibold text-primary transition-colors hover-darken"
        >
          Back to log in
        </NuxtLink>
      </p>
    </form>
  </AuthShell>
</template>
