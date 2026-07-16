<script setup lang="ts">
useHead({ title: 'Settings — FeedMe' })

const closeDrawer = inject(settingsDrawerCloseKey, () => {})

const { selectedUid, select } = useTapSelection()
</script>

<template>
  <!-- touch-none lets vaul own the touch gesture (drag-to-close); revisit
       per page once real content needs touch scrolling. -->
  <div class="h-full touch-none overflow-y-auto bg-default page-inset">
    <IconButton
      icon="i-ph-x-bold"
      aria-label="Close settings"
      @click="closeDrawer"
    />

    <h1 class="mt-lg text-title tracking-tight text-inset">
      Settings
    </h1>

    <ul class="mt-md flex flex-col text-inset">
      <li
        v-for="section in settingsSections"
        :key="section.to"
      >
        <NuxtLink
          :to="section.to"
          class="-mx-sm flex items-center gap-sm rounded-2xl px-sm py-sm text-body transition-colors"
          :class="selectedUid === section.to && 'bg-elevated shadow-elevated'"
          @pointerdown="select(section.to)"
        >
          <UIcon
            :name="section.icon"
            class="size-6 transition-colors duration-300 ease-out"
            :class="selectedUid === section.to ? 'text-primary' : 'text-muted'"
          />
          {{ section.label }}
        </NuxtLink>
      </li>
    </ul>
  </div>
</template>
