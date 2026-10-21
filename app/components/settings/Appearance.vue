<script setup lang="ts">
import { actionSides, paneSplits, postCardStyles, sidebarIconOptions, themes } from '~/stores/settings'

const settings = useSettingsStore()

// The panes and the sidebar only exist on desktop, so those controls are dead
// weight on a phone.
const isDesktop = useIsDesktop()
</script>

<template>
  <SettingsPage title="Appearance">
    <section>
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        Post cards
      </h3>
      <div class="mt-xs flex flex-col gap-px overflow-hidden rounded-2xl">
        <button
          v-for="option in postCardStyles"
          :key="option.name"
          type="button"
          :aria-pressed="settings.postCardStyle === option.name"
          class="flex items-center justify-between bg-elevated p-sm text-left"
          @click="settings.postCardStyle = option.name"
        >
          <span>{{ option.label }}</span>
          <UIcon
            v-if="settings.postCardStyle === option.name"
            name="i-ph-check-bold"
            class="size-5 text-primary"
          />
        </button>
      </div>
    </section>

    <section v-if="isDesktop">
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        Reading panes
      </h3>
      <div class="mt-xs flex flex-col gap-px overflow-hidden rounded-2xl">
        <button
          v-for="option in paneSplits"
          :key="option.name"
          type="button"
          :aria-pressed="settings.paneSplit === option.name"
          class="flex items-center justify-between bg-elevated p-sm text-left"
          @click="settings.paneSplit = option.name"
        >
          <span>{{ option.label }}</span>
          <UIcon
            v-if="settings.paneSplit === option.name"
            name="i-ph-check-bold"
            class="size-5 text-primary"
          />
        </button>
      </div>
    </section>

    <section v-if="isDesktop">
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        Sidebar icons
      </h3>
      <div class="mt-xs flex flex-col gap-px overflow-hidden rounded-2xl">
        <button
          v-for="option in sidebarIconOptions"
          :key="option.name"
          type="button"
          :aria-pressed="settings.sidebarIcons === option.name"
          class="flex items-center justify-between bg-elevated p-sm text-left"
          @click="settings.sidebarIcons = option.name"
        >
          <span>{{ option.label }}</span>
          <UIcon
            v-if="settings.sidebarIcons === option.name"
            name="i-ph-check-bold"
            class="size-5 text-primary"
          />
        </button>
      </div>
    </section>

    <section>
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        Post actions
      </h3>
      <div class="mt-xs flex flex-col gap-px overflow-hidden rounded-2xl">
        <button
          v-for="option in actionSides"
          :key="option.name"
          type="button"
          :aria-pressed="settings.actionSide === option.name"
          class="flex items-center justify-between bg-elevated p-sm text-left"
          @click="settings.actionSide = option.name"
        >
          <span>{{ option.label }}</span>
          <UIcon
            v-if="settings.actionSide === option.name"
            name="i-ph-check-bold"
            class="size-5 text-primary"
          />
        </button>
      </div>
    </section>

    <section>
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        Theme
      </h3>
      <div class="mt-xs flex flex-col gap-px overflow-hidden rounded-2xl">
        <button
          v-for="option in themes"
          :key="option.name"
          type="button"
          :aria-pressed="settings.theme === option.name"
          class="flex items-center justify-between bg-elevated p-sm text-left"
          @click="settings.theme = option.name"
        >
          <span>{{ option.label }}</span>
          <UIcon
            v-if="settings.theme === option.name"
            name="i-ph-check-bold"
            class="size-5 text-primary"
          />
        </button>
      </div>
    </section>
  </SettingsPage>
</template>
