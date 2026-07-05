<template>
  <div class="mx-auto flex min-h-dvh max-w-screen-sm flex-col">
    <!-- Positioning context + horizontal clip for the page-slide transitions.
         Each reader page renders its own Navbar so it slides with the page. -->
    <div class="relative grow overflow-x-clip">
      <slot />
    </div>

    <!-- Lives in the layout, outside the page-level Suspense: content changes
         inside the drawer must never interact with page rendering (they
         triggered page remounts when the drawer lived inside a page). -->
    <SettingsDrawer />
  </div>
</template>
