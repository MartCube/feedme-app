<script setup lang="ts">
useHead({ title: 'FeedMe' })

// Shared with the /settings/:panel? route (same component, see nuxt.config):
// a stable key keeps this page mounted across those navigations.
definePageMeta({ key: 'home' })

const { hasFeeds } = storeToRefs(useFeedsStore())
</script>

<template>
  <main class="flex flex-col page-inset">
    <Navbar>
      <IconButton
        icon="i-ph-list-bold"
        to="/settings"
        aria-label="Menu"
      />
      <IconButton
        icon="i-ph-plus-bold"
        to="/add"
        aria-label="Add"
      />
    </Navbar>

    <HomeFeedList
      v-if="hasFeeds"
      class="mt-lg"
    />
    <HomeEmptyState
      v-else
      class="grow"
    />
  </main>
</template>
