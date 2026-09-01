<script setup lang="ts">
// The app is login-only (backend.md § Auth), so this is the one route the
// global middleware lets through unauthenticated.
//
// layout: false is load-bearing — layouts/default.vue renders the desktop
// shell INSTEAD of the page slot above 1024px, so a default-layout login page
// would be invisible on desktop.
definePageMeta({ layout: false })
useHead({ title: 'Sign in' })

const auth = useAuthStore()

const token = ref('')
const pending = ref(false)
const failed = ref(false)

async function signIn() {
  if (!token.value.trim() || pending.value) return
  pending.value = true
  failed.value = false
  try {
    await auth.signIn(token.value)
    await navigateTo('/')
  }
  catch {
    // signIn proves the token against /me before keeping it, so this is the
    // only place a bad one is ever reported.
    failed.value = true
  }
  finally {
    pending.value = false
  }
}
</script>

<template>
  <main class="mx-auto flex min-h-dvh max-w-screen-sm flex-col justify-center gap-lg page-inset">
    <header class="flex flex-col gap-2xs">
      <h1 class="text-title tracking-tight">
        FeedMe
      </h1>
      <p class="text-body text-muted">
        Your feeds, in one calm place. Sign in to read them.
      </p>
    </header>

    <!-- The sign-in control is its own block, with nothing above depending on
         its size: T8 replaces this field with Google's rendered button, whose
         chrome Google owns and we can't restyle. -->
    <section class="flex flex-col gap-xs">
      <SearchInput
        v-model="token"
        placeholder="Paste your dev token"
        submit-label="Sign in"
        paste
        autofocus
        @submit="signIn"
      />
      <p
        v-if="failed"
        class="text-caption text-error text-inset"
      >
        That token isn't valid — mint a fresh one with manage.py issue_token.
      </p>
      <p
        v-else
        class="text-caption text-muted text-inset"
      >
        Google sign-in is coming; for now this takes a development token.
      </p>
    </section>
  </main>
</template>
