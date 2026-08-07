<script setup lang="ts">
// Desktop presentation of settings / add / edit: a full content page laid
// over the two reading panes (the sidebar stays interactive beside it). The
// panes underneath stay mounted and keep their scroll — that's the no-reload
// guarantee when closing back to the reader. Reuses the same panel components
// the mobile bottom sheets host.
const route = useRouter().currentRoute
const feedsStore = useFeedsStore()
const wizard = useAddFeedWizard()

const settingsPanel = computed(() => settingsPanels[route.value.path])
const onAdd = computed(() => route.value.path === '/add')
const onEdit = computed(() => route.value.path.startsWith('/edit/'))
const open = computed(() => Boolean(settingsPanel.value) || onAdd.value || onEdit.value)

// The mobile sheets reset the wizard when they finish closing; on desktop the
// equivalent moment is leaving the add/edit routes by any exit (done, close,
// sidebar click, browser back).
watch(() => onAdd.value || onEdit.value, (on, was) => {
  if (was && !on) wizard.reset()
})

function closeAdd() {
  navigateTo(feedsStore.readerPath)
}
</script>

<template>
  <div
    v-if="open"
    class="absolute inset-0 z-10 overflow-y-auto bg-default"
  >
    <!-- Left-aligned, not centred: the panels carry the same page-inset the
         sidebar does, so flush-left is what makes the two insets line up. -->
    <div class="h-full max-w-reading">
      <component
        :is="settingsPanel"
        v-if="settingsPanel"
        :key="route.path"
      />
      <AddSteps
        v-else-if="onAdd"
        @close="closeAdd"
        @done="closeAdd"
      />
      <EditPanels v-else />
    </div>
  </div>
</template>
