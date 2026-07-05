<!-- eslint-disable vue/multi-word-component-names -- docs/screens-and-flows.md names this component Navbar -->
<template>
  <!-- Rendered inside each reader page (not the layout) so it slides along
       with the page. Each page supplies its own buttons: content must be
       fixed per page instance, or the leaving page's icons would swap
       mid-slide when the route changes. -->
  <nav class="flex items-center justify-between">
    <slot />
  </nav>
</template>
