<script setup lang="ts">
import { feedListStyles, paneSplits, postCardStyles, scrollbarStyles, themes } from '~/stores/settings'

const settings = useSettingsStore()

// The scrollbar variants only apply to fine pointers and the panes only exist
// on desktop, so both controls are dead weight on a phone.
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

    <section>
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        Feed list
      </h3>
      <div class="mt-xs flex flex-col gap-px overflow-hidden rounded-2xl">
        <button
          v-for="option in feedListStyles"
          :key="option.name"
          type="button"
          :aria-pressed="settings.feedListStyle === option.name"
          class="flex items-center justify-between bg-elevated p-sm text-left"
          @click="settings.feedListStyle = option.name"
        >
          <span>{{ option.label }}</span>
          <UIcon
            v-if="settings.feedListStyle === option.name"
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

    <section v-if="isDesktop">
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        Scrollbar
      </h3>
      <div class="mt-xs flex flex-col gap-px overflow-hidden rounded-2xl">
        <button
          v-for="option in scrollbarStyles"
          :key="option.name"
          type="button"
          :aria-pressed="settings.scrollbarStyle === option.name"
          class="flex items-center justify-between bg-elevated p-sm text-left"
          @click="settings.scrollbarStyle = option.name"
        >
          <span>{{ option.label }}</span>
          <UIcon
            v-if="settings.scrollbarStyle === option.name"
            name="i-ph-check-bold"
            class="size-5 text-primary"
          />
        </button>
      </div>
    </section>
  </SettingsPage>
</template>
