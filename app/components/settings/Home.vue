<script setup lang="ts">
useHead({ title: 'Settings — FeedMe' })

// `activePath` is the desktop master–detail selection: the section open in the
// detail pane keeps the elevated row. The mobile sheet passes none — there the
// list slides away behind the section anyway.
const props = defineProps<{ activePath?: string }>()

const closeDrawer = inject(settingsDrawerCloseKey, () => {})

const { selectedUid, select } = useTapSelection()

// Mobile tap flash OR persistent desktop selection — same rule as the feed
// list's rows, and the same treatment: the label goes primary and the row
// takes the elevated surface.
function isActive(to: string) {
  return selectedUid.value === to || props.activePath === to
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
            class="size-6 transition-colors duration-300 ease-out"
            :class="isActive(section.to) ? 'text-primary' : 'text-muted [@media(hover:hover)]:group-hover:text-primary'"
          />
          {{ section.label }}
        </NuxtLink>
      </li>
    </ul>
  </div>
</template>
