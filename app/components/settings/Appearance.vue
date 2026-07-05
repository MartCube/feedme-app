<script setup lang="ts">
</script>

<template>
  <SettingsPage title="Appearance">
    <section>
      <h3 class="text-xs font-semibold uppercase tracking-wide text-muted">
        Cards
      </h3>
      <div class="mt-3 flex flex-col gap-px overflow-hidden rounded-2xl">
        <div class="flex items-center justify-between bg-elevated p-4">
          <span>Card style</span>
          <span class="text-sm text-muted">Detailed</span>
        </div>
        <div class="flex items-center justify-between bg-elevated p-4">
          <span>Font size</span>
          <span class="text-sm text-muted">100%</span>
        </div>
      </div>
      <p class="mt-3 text-sm text-muted">
        These settings apply to post cards in feed lists. Mock content for now.
      </p>
    </section>

    <section>
      <h3 class="text-xs font-semibold uppercase tracking-wide text-muted">
        Theme
      </h3>
      <div class="mt-3 flex items-center justify-between rounded-2xl bg-elevated p-4">
        <span>Theme</span>
        <span class="text-sm text-muted">Dark</span>
      </div>
    </section>
  </SettingsPage>
</template>
