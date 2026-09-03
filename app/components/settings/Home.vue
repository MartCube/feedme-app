<script setup lang="ts">
useHead({ title: 'Settings — FeedMe' })

// `activePath` is the desktop master–detail selection: the section open in the
// detail pane keeps the elevated row. The mobile sheet passes none — there the
// list slides away behind the section anyway.
defineProps<{ activePath?: string }>()

const closeDrawer = inject(settingsDrawerCloseKey, () => {})

const { selectedUid, select } = useTapSelection()
</script>

<template>
  <!-- touch-none lets vaul own the touch gesture (drag-to-close); revisit
       per page once real content needs touch scrolling. -->
  <div class="h-full touch-none scroll-host bg-default page-inset">
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
          :class="selectedUid === section.to || activePath === section.to ? 'bg-elevated shadow-elevated' : 'hover-highlight'"
          @pointerdown="select(section.to)"
        >
          <UIcon
            :name="section.icon"
            class="size-6 transition-colors duration-300 ease-out"
            :class="selectedUid === section.to || activePath === section.to ? 'text-primary' : 'text-muted'"
          />
          {{ section.label }}
        </NuxtLink>
      </li>
    </ul>
  </div>
</template>
