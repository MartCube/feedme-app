<script setup lang="ts">
// Desktop presentation of settings / add / edit: a content area laid over the
// two reading panes (the sidebar stays interactive beside it), split into the
// same master–detail pair the reader uses — the flow's list on the left, what
// it opens on the right. The panes underneath stay mounted and keep their
// scroll; that's the no-reload guarantee when closing back to the reader.
// Reuses the same panel components the mobile bottom sheets host.
//
// Switching detail is a plain swap, exactly like clicking a different post:
// the master stays put and nothing slides. Only the area as a whole slides,
// in from the right when it opens (.content-slide-*, transitions.css) — which
// is the desktop equivalent of the page push mobile gets.
const route = useRouter().currentRoute
const feedsStore = useFeedsStore()
const wizard = useAddFeedWizard()

// Settings: the section list is the master, the open section the detail.
// /settings alone has no detail — settingsPanels maps it to the list itself.
const onSettings = computed(() => Boolean(settingsPanels[route.value.path]))
const settingsDetail = computed(() =>
  route.value.path === '/settings' ? undefined : settingsPanels[route.value.path],
)

const onAdd = computed(() => route.value.path === '/add')

// Gated on the store like the mobile sheet (edit/Drawer.vue): the edit panels
// render from the folder or feed the URL names. Settings and add need none of
// that, so they don't wait.
const { loaded, unreachable } = storeToRefs(feedsStore)
const onEdit = computed(() =>
  route.value.path.startsWith('/edit/') && (loaded.value || unreachable.value),
)
// 'edit' is the bare /edit/:uid record; every other edit route names something
// deeper, which is what the detail pane renders.
const editDetail = computed(() => onEdit.value && route.value.name !== 'edit')
// A folder's members are a list to pick from, so it earns the split. A loose
// feed has nothing below it — a second pane there would just be dead space
// beside a squeezed form, so it takes the area whole like the add wizard.
const editIsFolder = computed(() => String(route.value.params.uid ?? '').startsWith('folder_'))
const single = computed(() => onAdd.value || (onEdit.value && !editIsFolder.value))

const open = computed(() => onSettings.value || onAdd.value || onEdit.value)

const placeholder = computed(() => onSettings.value ? 'Select a section' : 'Select a feed')

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
  <Transition name="content-slide">
    <div
      v-if="open"
      class="absolute inset-0 z-10 flex bg-default"
    >
      <!-- Flows with no list to sit beside: the add wizard (four linear steps)
           and a loose feed's edit. Left-aligned, not centred — the panel
           carries the same page-inset the sidebar does, and flush-left is what
           makes the two insets line up. -->
      <section
        v-if="single"
        class="min-w-0 w-full max-w-reading"
      >
        <AddSteps
          v-if="onAdd"
          @close="closeAdd"
          @done="closeAdd"
        />
        <EditPanels
          v-else
          pane="single"
        />
      </section>

      <!-- Same 40/60 split as the reading panes. Each panel brings its own
           scroll-host and page-inset, so the sections only carry the measure. -->
      <template v-else>
        <section class="basis-2/5 shrink-0">
          <SettingsHome
            v-if="onSettings"
            :active-path="route.path"
          />
          <EditPanels
            v-else
            pane="master"
          />
        </section>

        <section class="min-w-0 basis-3/5">
          <component
            :is="settingsDetail"
            v-if="settingsDetail"
            :key="route.path"
          />
          <EditPanels
            v-else-if="editDetail"
            pane="detail"
          />
          <div
            v-else-if="placeholder"
            class="flex h-full items-center justify-center"
          >
            <p class="text-body text-dimmed">
              {{ placeholder }}
            </p>
          </div>
        </section>
      </template>
    </div>
  </Transition>
</template>
