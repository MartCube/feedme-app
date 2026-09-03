<script setup lang="ts">
// Desktop sidebar: the shared home feed list, then the two standing entries —
// Add feed and Settings. Both are plain rows shaped like a feed row. The
// settings sections themselves are NOT listed here: the content area renders
// them in its master pane (desktop/ContentOverlay.vue), and having the same
// four links in both places put one list beside its own copy.
// bg-sunken is what separates the sidebar from the reading panes — one step
// below the page, so the elevated selected row still reads on top of it.
// vue-router's live route (see Shell.vue — Nuxt's useRoute() doesn't update
// without a rendered NuxtPage).
const route = useRouter().currentRoute
const { readerFeedUid } = storeToRefs(useFeedsStore())
</script>

<template>
  <aside class="flex h-full flex-col scroll-host bg-sunken page-inset">
    <HomeFeedList :active-uid="readerFeedUid" />

    <NuxtLink
      to="/add"
      class="-mx-sm mt-md flex items-center gap-sm rounded-2xl px-sm py-sm text-body text-muted transition-colors"
      :class="route.path === '/add' ? 'bg-elevated shadow-elevated' : 'hover-highlight'"
    >
      <UIcon
        name="i-ph-plus-bold"
        class="size-5"
      />
      Add feed
    </NuxtLink>

    <NuxtLink
      to="/settings"
      class="-mx-sm flex items-center gap-sm rounded-2xl px-sm py-sm text-body text-muted transition-colors"
      :class="route.path.startsWith('/settings') ? 'bg-elevated shadow-elevated' : 'hover-highlight'"
    >
      <UIcon
        name="i-ph-gear-bold"
        class="size-5"
      />
      Settings
    </NuxtLink>
  </aside>
</template>
