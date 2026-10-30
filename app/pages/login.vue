<script setup lang="ts">
// Both signed-out screens: /login, and /signup, which nuxt.config.ts routes to
// this same component under the same key. The middleware lets exactly these
// two through signed out. Switching between them keeps this instance — only
// the copy and the form's mode change — so the drift, the card and Google's
// button stay where they are, and the stacked copy (AuthShell, the footer
// below) keeps every control on the same spot.
//
// layout: false is load-bearing — layouts/default.vue renders the desktop
// shell INSTEAD of the page slot above 1024px, so a default-layout login page
// would be invisible on desktop.
definePageMeta({ layout: false, key: 'auth' })

// useRouter().currentRoute rather than useRoute(): this instance outlives the
// navigation between the two paths, and has to follow it.
const route = useRouter().currentRoute
const mode = computed(() => route.value.path === '/signup' ? 'signup' : 'login')

const copy = {
  login: {
    hero: ['All your feeds,', 'in one calm place.'],
    lede: 'Websites, YouTube channels and subreddits in a single, quiet reading list.',
  },
  signup: {
    hero: ['Start your', 'calm feed.'],
    lede: 'Add the websites, channels and subreddits you follow, and read them in one place.',
  },
} as const

const form = {
  login: { heading: 'Log in', submit: 'Log in with email' },
  signup: { heading: 'Create account', submit: 'Sign up with email' },
} as const

useHead({ title: () => form[mode.value].heading })
</script>

<template>
  <AuthShell
    :mode="mode"
    :copy="copy"
  >
    <AuthForm
      :mode="mode"
      :heading="form[mode].heading"
      :submit-label="form[mode].submit"
    >
      <!-- Both footers in one cell, the inactive one invisible: the cell is
           the height of the taller, so the form never moves on a switch. -->
      <div class="grid">
        <div
          class="col-start-1 row-start-1 flex flex-col justify-end transition-opacity"
          :class="mode === 'login' ? 'opacity-100' : 'invisible opacity-0'"
        >
          <p class="text-center text-caption text-muted">
            New to FeedMe?
            <NuxtLink
              to="/signup"
              replace
              class="font-semibold text-primary transition-colors hover-darken"
            >
              Create an account
            </NuxtLink>
          </p>
        </div>
        <div
          class="col-start-1 row-start-1 flex flex-col gap-sm transition-opacity"
          :class="mode === 'signup' ? 'opacity-100' : 'invisible opacity-0'"
        >
          <!-- Not links yet: neither page exists, and a link to a 404 is
               worse than none. nowrap keeps each name whole; balance keeps a
               word from being left alone on the last line. -->
          <p class="text-center text-caption text-balance text-muted">
            By signing up you agree to our <span class="whitespace-nowrap">Terms</span>
            and <span class="whitespace-nowrap">Privacy Policy</span>.
          </p>
          <p class="text-center text-caption text-muted">
            Already have an account?
            <NuxtLink
              to="/login"
              replace
              class="font-semibold text-primary transition-colors hover-darken"
            >
              Log in
            </NuxtLink>
          </p>
        </div>
      </div>
    </AuthForm>
  </AuthShell>
</template>
