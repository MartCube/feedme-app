<script setup lang="ts">
useHead({ title: 'Settings — FeedMe' })

const closeDrawer = inject(settingsDrawerCloseKey, () => {})

const sections = [
  { label: 'Account', icon: 'i-ph-user-bold', to: '/settings/account' },
  { label: 'Appearance', icon: 'i-ph-paint-brush-broad-bold', to: '/settings/appearance' },
  { label: 'About', icon: 'i-ph-info-bold', to: '/settings/about' },
  { label: 'Report an issue', icon: 'i-ph-bug-bold', to: '/settings/report' },
]
</script>

<template>
  <!-- touch-none lets vaul own the touch gesture (drag-to-close); revisit
       per page once real content needs touch scrolling. -->
  <div class="h-full touch-none overflow-y-auto bg-default px-md pt-lg pb-xl">
    <IconButton
      icon="i-ph-x-bold"
      aria-label="Close settings"
      @click="closeDrawer"
    />

    <h1 class="mt-lg text-title tracking-tight">
      Settings
    </h1>

    <ul class="mt-md flex flex-col">
      <li
        v-for="section in sections"
        :key="section.to"
      >
        <NuxtLink
          :to="section.to"
          class="flex items-center gap-sm py-sm text-body"
        >
          <UIcon
            :name="section.icon"
            class="size-6 text-muted"
          />
          {{ section.label }}
        </NuxtLink>
      </li>
    </ul>
  </div>
</template>
