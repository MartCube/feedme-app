<script setup lang="ts">
import { themes } from '~/stores/settings'

const settings = useSettingsStore()
</script>

<template>
  <SettingsPage title="Appearance">
    <section>
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted">
        Cards
      </h3>
      <div class="mt-3 flex flex-col gap-px overflow-hidden rounded-2xl">
        <div class="flex items-center justify-between bg-elevated p-4">
          <span>Card style</span>
          <span class="text-caption text-muted">Detailed</span>
        </div>
        <div class="flex items-center justify-between bg-elevated p-4">
          <span>Font size</span>
          <span class="text-caption text-muted">100%</span>
        </div>
      </div>
      <p class="mt-3 text-caption text-muted">
        These settings apply to post cards in feed lists. Mock content for now.
      </p>
    </section>

    <section>
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted">
        Theme
      </h3>
      <div class="mt-3 flex flex-col gap-px overflow-hidden rounded-2xl">
        <button
          v-for="option in themes"
          :key="option.name"
          type="button"
          :aria-pressed="settings.theme === option.name"
          class="flex items-center justify-between bg-elevated p-4 text-left"
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
