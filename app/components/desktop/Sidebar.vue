<script setup lang="ts">
// Desktop sidebar: the shared home feed list (plus the Add feed entry), then
// a collapsible Settings section for the subpage links — its header is shaped
// like the feed list's folder rows so the two dropdowns read as one control.
// Open state persists via the settings store; the feed list itself is the
// same component the mobile home page renders.
// bg-sunken is what separates the sidebar from the reading panes — one step
// below the page, so the elevated selected row still reads on top of it.
// vue-router's live route (see Shell.vue — Nuxt's useRoute() doesn't update
// without a rendered NuxtPage).
const route = useRouter().currentRoute
const settings = useSettingsStore()
const { readerFeedUid } = storeToRefs(useFeedsStore())
</script>

<template>
  <aside class="flex h-full flex-col overflow-y-auto bg-sunken page-inset">
    <HomeFeedList :active-uid="readerFeedUid" />
    <NuxtLink
      to="/add"
      class="-mx-sm mt-md flex items-center gap-xs rounded-2xl px-sm py-sm text-body text-muted transition-colors"
      :class="route.path === '/add' && 'bg-elevated shadow-elevated'"
    >
      <UIcon
        name="i-ph-plus-bold"
        class="size-5"
      />
      Add feed
    </NuxtLink>

    <!-- Settings section. Same metrics as a folder row in the feed list:
         text-body label, size-6 caret in a size-12 hit box. -->
    <button
      type="button"
      class="-mx-sm mt-lg flex items-center rounded-2xl"
      :aria-expanded="settings.sidebarSettingsOpen"
      :aria-label="settings.sidebarSettingsOpen ? 'Collapse settings' : 'Expand settings'"
      @click="settings.sidebarSettingsOpen = !settings.sidebarSettingsOpen"
    >
      <span class="min-w-0 flex-1 py-sm pl-sm text-left text-body">Settings</span>
      <span
        class="mr-sm flex size-12 shrink-0 items-center justify-center transition-transform duration-200"
        :class="settings.sidebarSettingsOpen && 'rotate-90'"
      >
        <UIcon
          name="i-ph-caret-right-bold"
          class="size-6"
        />
      </span>
    </button>
    <ul
      v-if="settings.sidebarSettingsOpen"
      class="flex flex-col"
    >
      <li
        v-for="section in settingsSections"
        :key="section.to"
      >
        <NuxtLink
          :to="section.to"
          class="-mx-sm flex items-center gap-sm rounded-2xl px-sm py-sm text-body transition-colors"
          :class="route.path === section.to && 'bg-elevated shadow-elevated'"
        >
          <UIcon
            :name="section.icon"
            class="size-5 text-muted"
          />
          {{ section.label }}
        </NuxtLink>
      </li>
    </ul>
  </aside>
</template>
