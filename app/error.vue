<script setup lang="ts">
import type { NuxtError } from '#app'

// The app-level error page: a missing route (404) gets the "isn't in your
// feed" copy, anything else a generic version of the same layout.
//
// Nuxt renders this INSTEAD of app.vue, so what app.vue provides has to be
// restated here — the theme attribute (or a 404 would always paint in Ink)
// and UApp (IconButton's tooltip needs its provider). A signed-out visitor
// never gets here: the global middleware sends every route to /login first.
const props = defineProps<{ error: NuxtError }>()

const { theme } = storeToRefs(useSettingsStore())
useHead({
  htmlAttrs: { 'data-theme': theme },
  title: () => props.error.statusCode === 404 ? 'Page not found' : 'Something went wrong',
})

const notFound = computed(() => props.error.statusCode === 404)
const copy = computed(() => notFound.value
  ? {
      label: 'Error 404',
      title: 'This page isn’t in your feed',
      body: 'The link may be out of date, or the post was removed by its source.',
    }
  : {
      label: `Error ${props.error.statusCode || ''}`.trim(),
      title: 'Something went wrong',
      body: 'FeedMe couldn’t open this page. Your feeds are fine — try again from the list.',
    })

// Back where you came from when there is somewhere to go back to (vue-router
// records it on history.state); a link opened cold has nowhere, so home.
async function goBack() {
  const back = window.history.state?.back
  await clearError(back ? {} : { redirect: '/' })
  if (back) useRouter().back()
}
</script>

<template>
  <UApp>
    <main class="flex min-h-dvh flex-col page-inset">
      <div class="lg:hidden">
        <IconButton
          icon="i-ph-caret-left-bold"
          aria-label="Back"
          @click="goBack"
        />
      </div>
      <!-- Desktop: the brand in the corner, as the shell's sidebar would have it. -->
      <p class="hidden items-center gap-xs text-logo tracking-tight lg:flex">
        <Logo class="size-8" />
        <span><span class="text-primary">Feed</span>Me</span>
      </p>

      <div class="flex flex-1 flex-col justify-center gap-lg py-lg lg:mx-auto lg:w-full lg:max-w-reading lg:items-center lg:text-center">
        <!-- The mark with its right-hand page missing: the left stack as
             always, the right only as a dashed outline of where it should be. -->
        <svg
          viewBox="0 0 64 64"
          role="img"
          aria-label="An open book with its right page missing"
          class="size-32 shrink-0 lg:size-44"
        >
          <g class="fill-current text-primary">
            <path d="M30 17L9 11.5a3 3 0 0 0-3.8 2.9v2a3 3 0 0 0 2.2 2.9L30 25z" />
            <path d="M30 29.5L9 24a3 3 0 0 0-3.8 2.9v2a3 3 0 0 0 2.2 2.9L30 37.5z" />
            <path d="M30 42L9 36.5a3 3 0 0 0-3.8 2.9v2a3 3 0 0 0 2.2 2.9L30 50z" />
          </g>
          <g
            class="fill-none stroke-current text-dimmed"
            stroke-width="1.2"
            stroke-dasharray="2.4 2"
          >
            <path d="M34 17L55 11.5a3 3 0 0 1 3.8 2.9v2a3 3 0 0 1-2.2 2.9L34 25z" />
            <path d="M34 29.5L55 24a3 3 0 0 1 3.8 2.9v2a3 3 0 0 1-2.2 2.9L34 37.5z" />
            <path d="M34 42L55 36.5a3 3 0 0 1 3.8 2.9v2a3 3 0 0 1-2.2 2.9L34 50z" />
          </g>
        </svg>

        <div class="flex flex-col gap-xs lg:items-center">
          <p class="text-caption font-semibold uppercase tracking-widest text-primary">
            {{ copy.label }}
          </p>
          <h1 class="text-hero text-balance">
            {{ copy.title }}
          </h1>
          <p class="text-body text-muted">
            {{ copy.body }}
          </p>
        </div>

        <!-- Desktop: an inline pair under the copy. Phone: stacked at the
             bottom of the screen, where a thumb is. -->
        <nav class="hidden gap-sm lg:flex">
          <BlockButton
            variant="filled"
            label="Back to your feeds"
            class="px-lg lg:w-auto"
            @click="clearError({ redirect: '/' })"
          />
          <BlockButton
            label="Open Saved"
            class="px-lg lg:w-auto"
            @click="clearError({ redirect: '/feed/saved' })"
          />
        </nav>
      </div>

      <nav class="flex flex-col gap-sm lg:hidden">
        <BlockButton
          variant="filled"
          label="Back to your feeds"
          @click="clearError({ redirect: '/' })"
        />
        <BlockButton
          label="Open Saved"
          @click="clearError({ redirect: '/feed/saved' })"
        />
      </nav>
    </main>
  </UApp>
</template>
