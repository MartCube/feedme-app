<script setup lang="ts">
// The desktop keyboard map. A reference only: each binding lives in the
// component that owns its state (DesktopShell for Esc, FeedPostList for the
// rest), so a new shortcut is its binding there plus its row here. Keys are
// UKbd names — it renders arrowdown as ↓, escape as Esc, enter as ↵.
const groups = [
  {
    title: 'Reading',
    rows: [
      { label: 'Next post', keys: ['arrowdown'] },
      { label: 'Previous post', keys: ['arrowup'] },
      { label: 'Search this list', keys: ['/'] },
    ],
  },
  {
    title: 'Search',
    rows: [
      { label: 'Done typing — arrows step through results', keys: ['enter'] },
      { label: 'Close the search', keys: ['escape'] },
    ],
  },
  {
    title: 'Anywhere',
    rows: [
      { label: 'Close Settings, Add, an edit, or the open post', keys: ['escape'] },
    ],
  },
]
</script>

<template>
  <SettingsPage title="Keyboard shortcuts">
    <section
      v-for="group in groups"
      :key="group.title"
    >
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        {{ group.title }}
      </h3>
      <div class="mt-xs flex flex-col gap-px overflow-hidden rounded-2xl">
        <div
          v-for="row in group.rows"
          :key="row.label"
          class="flex items-center justify-between gap-sm bg-elevated p-sm"
        >
          <span>{{ row.label }}</span>
          <span class="flex shrink-0 gap-2xs">
            <!-- The cap sits one surface up from the row, no ring
                 (design-system: no gloss, elevation by surface). -->
            <UKbd
              v-for="key in row.keys"
              :key="key"
              :value="key"
              size="lg"
              variant="soft"
              :ui="{ base: 'h-6 min-w-6 bg-muted text-default normal-case text-body rounded-lg px-xs' }"
            />
          </span>
        </div>
      </div>
    </section>
  </SettingsPage>
</template>
