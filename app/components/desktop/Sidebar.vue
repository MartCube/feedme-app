<script setup lang="ts">
// Desktop sidebar, three groups: the pinned rows (Home, Saved, New Feed), the
// feeds, and the settings sections right after them. Feeds and Settings fold
// under a caption header, remembered per device (settings store). The
// sections are listed here directly, so one click opens one — on desktop the
// post pane's own section list is never shown beside this one.
// bg-sunken is what separates the sidebar from the reading panes — one step
// below the page, so the elevated selected row still reads on top of it.
// vue-router's live route (see Shell.vue — Nuxt's useRoute() doesn't update
// without a rendered NuxtPage).
const route = useRouter().currentRoute
const { readerFeedUid } = storeToRefs(useFeedsStore())
const settings = useSettingsStore()

const onAdd = computed(() => route.value.path === '/add')
const icons = computed(() => settings.sidebarIcons === 'shown')

// The rows' fold slide (fold-rows, motion.css) waits for the first toggle:
// the group mounts open on page load, and the rows would slide in.
const settingsFolded = ref(false)

// The icons rest muted, a step quieter than their labels, so they follow the
// row's hover accent by the same gate instead of inheriting it (as in
// settings/Home.vue).
function iconClass(active: boolean) {
  return active ? 'text-primary' : 'text-muted [@media(hover:hover)]:group-hover:text-primary'
}
</script>

<template>
  <aside class="flex h-full flex-col scroll-host bg-sunken page-inset">
    <!-- contents: the list's rows join the aside directly, so the pinned
         wordmark's sticky range is the whole sidebar — inside the list's own
         box it would scroll off as the lower groups come into view. -->
    <HomeFeedList
      :active-uid="readerFeedUid"
      grouped
      :icons="icons"
      class="contents!"
    >
      <!-- New Feed rides the pinned rows' treatment, so it's a card beside
           them in cards mode, and stays selected like them while its wizard
           is open in the post pane. -->
      <template #pinned="{ rowClass }">
        <li
          class="-mx-sm rounded-2xl transition-colors"
          :class="rowClass('add', onAdd)"
        >
          <NuxtLink
            to="/add"
            class="group flex min-w-0 items-center gap-sm px-sm py-xs"
          >
            <UIcon
              v-if="icons"
              name="i-ph-plus-bold"
              class="size-5 shrink-0 transition-colors"
              :class="iconClass(onAdd)"
            />
            <span class="truncate text-body">New Feed</span>
          </NuxtLink>
        </li>
      </template>
    </HomeFeedList>

    <!-- Right under the feeds, on the same group gap — not pushed to the
         bottom, where it jumped while the feeds above it folded. Same fold,
         fade and bleed treatment as Feeds (HomeFeedList). -->
    <UCollapsible
      v-model:open="settings.settingsGroupOpen"
      class="mt-lg flex flex-col"
      :ui="{ content: '-mx-sm px-sm data-[state=open]:animate-[collapsible-down_200ms_var(--ease-out),fade-in_200ms_var(--ease-out)] data-[state=closed]:animate-[collapsible-up_200ms_var(--ease-out),fade-out_200ms_var(--ease-out)]' }"
      @update:open="settingsFolded = true"
    >
      <template #default="{ open }">
        <GroupToggle
          label="Settings"
          :open="open"
        />
      </template>
      <template #content>
        <!-- pt, not mt: a margin would collapse through the content box
             whenever it isn't clipping, and the rows' slide moves by the
             box's height. -->
        <ul
          class="flex flex-col gap-2xs pt-xs"
          :class="settingsFolded && 'fold-rows'"
        >
          <li
            v-for="section in settingsSections"
            :key="section.to"
          >
            <NuxtLink
              :to="section.to"
              class="group -mx-sm flex items-center gap-sm rounded-2xl px-sm py-xs text-body transition-colors"
              :class="route.path === section.to ? 'bg-elevated shadow-elevated text-primary' : 'hover-accent'"
            >
              <UIcon
                v-if="icons"
                :name="section.icon"
                class="size-5 transition-colors"
                :class="iconClass(route.path === section.to)"
              />
              {{ section.label }}
            </NuxtLink>
          </li>
        </ul>
      </template>
    </UCollapsible>
  </aside>
</template>
