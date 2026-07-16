<script setup lang="ts">
</script>

<template>
  <SettingsPage title="Account">
    <section>
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        Signed in with
      </h3>
      <div class="mt-xs flex flex-col gap-px overflow-hidden rounded-2xl">
        <div class="flex items-center gap-sm bg-elevated p-sm">
          <UIcon
            name="i-ph-google-logo-bold"
            class="size-6 text-muted"
          />
          <span>Google</span>
          <span class="ml-auto text-caption text-muted">martin@gmail.com</span>
        </div>
        <div class="flex items-center justify-between bg-elevated p-sm">
          <span>Member since</span>
          <span class="text-caption text-muted">May 2026</span>
        </div>
      </div>
    </section>

    <section>
      <div class="rounded-2xl bg-elevated p-sm text-error">
        Sign out
      </div>
    </section>
  </SettingsPage>
</template>
