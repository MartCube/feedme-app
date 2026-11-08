<script setup lang="ts">
// The frame of the signed-out screen: the drifting feed, the brand, a
// two-line hero (second line in the accent), one line of what FeedMe is, and
// the form in the slot.
//
// Phone: everything sits at the bottom of the screen, the drift above it.
// Desktop: the same content in a card centred over a full-page drift.
//
// Every mode's hero is rendered, stacked in one grid cell with only the
// active one visible, so the cell is always as tall as the longest. Switching
// between log in and sign up then moves nothing: the copy changes in place.
// `invisible` takes the others out of the accessibility tree as well. Login
// has two modes; the email-link screens (reset password, confirm email) pass
// theirs the same way.
defineProps<{
  mode: string
  copy: Record<string, { hero: readonly [string, string], lede: string }>
}>()
</script>

<template>
  <main class="relative flex h-dvh min-h-fit flex-col overflow-hidden page-inset lg:items-center lg:justify-center">
    <AuthDrift />

    <div class="relative flex flex-col gap-lg lg:w-full lg:max-w-auth lg:rounded-sheet lg:bg-default lg:p-lg lg:shadow-elevated">
      <div class="flex flex-col gap-md">
        <!-- The app's wordmark, as at the top of the feed list (home/FeedList.vue):
             Feed in the accent, Me in body ink, like the mark's two stacks. -->
        <p class="flex items-center gap-xs text-logo tracking-tight">
          <Logo class="size-10" />
          <span><span class="text-primary">Feed</span>Me</span>
        </p>

        <div class="grid">
          <header
            v-for="(text, key) in copy"
            :key="key"
            class="col-start-1 row-start-1 flex flex-col gap-xs transition-opacity"
            :class="key === mode ? 'opacity-100' : 'invisible opacity-0'"
          >
            <h1 class="text-hero">
              <span class="block">{{ text.hero[0] }}</span>
              <span class="block text-primary">{{ text.hero[1] }}</span>
            </h1>
            <p class="text-body text-muted">
              {{ text.lede }}
            </p>
          </header>
        </div>
      </div>

      <slot />
    </div>
  </main>
</template>
