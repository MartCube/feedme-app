<script setup lang="ts">
useHead({ title: 'Settings — FeedMe' })

const closeDrawer = inject(settingsDrawerCloseKey, () => {})

const { selectedUid, select } = useTapSelection()

// The tap flash — same treatment as the feed list's rows: the label goes
// primary and the row takes the elevated surface. A section replaces this
// list on both phone and desktop, so there's no standing selection to show.
function isActive(to: string) {
  return selectedUid.value === to
}
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
          class="group -mx-sm flex items-center gap-sm rounded-2xl px-sm py-sm text-body transition-colors"
          :class="isActive(section.to) ? 'bg-elevated shadow-elevated text-primary' : 'hover-accent'"
          @pointerdown="select(section.to)"
        >
          <!-- The icon sets its own colour, so it can't inherit the row's
               hover accent — it follows by the same gate instead, or the label
               would light up beside a muted icon. -->
          <UIcon
            :name="section.icon"
            class="size-6 transition-colors"
            :class="isActive(section.to) ? 'text-primary' : 'text-muted [@media(hover:hover)]:group-hover:text-primary'"
          />
          {{ section.label }}
        </NuxtLink>
      </li>
    </ul>
  </div>
</template>
