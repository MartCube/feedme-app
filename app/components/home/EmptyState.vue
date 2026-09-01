<script setup lang="ts">
// Two ways the home screen has nothing to list, sharing one layout: the
// first-run nudge (nothing followed yet → point straight at the add flow), and
// an API that didn't answer — which must not masquerade as an empty account.
// Rendered by the mobile home page and, on desktop, in place of the two
// reading panes.
const feedsStore = useFeedsStore()
const { unreachable } = storeToRefs(feedsStore)
</script>

<template>
  <div class="mx-auto flex max-w-postlist flex-col items-center justify-center gap-md text-center page-inset">
    <template v-if="unreachable">
      <h2 class="text-title tracking-tight">
        Can't reach the server
      </h2>
      <p class="text-body text-muted">
        Your feeds are there — we just couldn't load them.
      </p>
      <BlockButton
        label="Try again"
        icon="i-ph-arrow-counter-clockwise-bold"
        @click="feedsStore.load()"
      />
    </template>

    <template v-else>
      <h2 class="text-title tracking-tight">
        Nothing here yet
      </h2>
      <p class="text-body text-muted">
        Follow a website, YouTube channel, or subreddit — new posts land here, all in one calm place.
      </p>
      <BlockButton
        label="Add your first feed"
        icon="i-ph-plus-bold"
        variant="primary"
        @click="navigateTo('/add')"
      />
    </template>
  </div>
</template>
