<script setup lang="ts">
// Single branch point between the mobile tree and the desktop shell.
// useIsDesktop is false during SSR and hydration, so the server always emits
// the mobile tree; on a wide client lg:hidden masks it at first paint until
// the ref flips after mount and the desktop shell takes over. NuxtPage (the
// slot) is not rendered at all on desktop — the shell composes its panes from
// the route + stores instead, so the page/slide machinery never runs there.
const isDesktop = useIsDesktop()
</script>

<template>
  <div
    v-if="!isDesktop"
    class="mx-auto flex min-h-dvh max-w-screen-sm flex-col lg:hidden"
  >
    <!-- Positioning context + horizontal clip for the page-slide transitions.
         Each reader page renders its own Navbar so it slides with the page. -->
    <div class="relative grow overflow-x-clip">
      <slot />
    </div>

    <!-- Lives in the layout, outside the page-level Suspense: content changes
         inside the drawer must never interact with page rendering (they
         triggered page remounts when the drawer lived inside a page). -->
    <SettingsDrawer />
    <AddDrawer />
  </div>

  <DesktopShell v-else />
</template>
