<script setup lang="ts">
// Desktop presentation of settings / add: a content area laid over the
// two reading panes (the sidebar stays interactive beside it), split into the
// same master–detail pair the reader uses — the flow's list on the left, what
// it opens on the right. The panes underneath stay mounted and keep their
// scroll; that's the no-reload guarantee when closing back to the reader.
// Reuses the same panel components the mobile bottom sheets host.
//
// Nothing here animates. Opening the area is a page replacing a page, and
// switching detail is a plain swap, exactly like clicking a different post.
// Sliding is the mobile stack's language: there, one pane is the whole screen
// and the motion is what tells you which way you moved. Here both ends of the
// move are on screen at once, so it would only be decoration.
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

const open = computed(() => onSettings.value || onAdd.value)

// The mobile sheet resets the wizard when it finishes closing; on desktop the
// equivalent moment is leaving /add by any exit (done, close, sidebar click,
// browser back).
watch(onAdd, (on, was) => {
  if (was && !on) wizard.reset()
})

function closeAdd() {
  navigateTo(feedsStore.readerPath)
}
</script>

<template>
  <div
    v-if="open"
    class="absolute inset-0 z-10 flex bg-default"
  >
    <!-- The add wizard has no list to sit beside (four linear steps).
         Left-aligned, not centred — the panel carries the same page-inset the
         sidebar does, and flush-left is what makes the two insets line up. -->
    <section
      v-if="onAdd"
      class="min-w-0 w-full max-w-reading"
    >
      <AddSteps
        :slide="false"
        @close="closeAdd"
        @done="closeAdd"
      />
    </section>

    <!-- Two equal panes, NOT the reader's 40/60. A form is not an article: it
         doesn't get wider-and-better, it just gets a longer line to read a
         label across. Equal columns keep the detail at the master's measure
         and leave the remainder empty on the right, which is the correct
         answer for content that has a natural width. Each panel brings its
         own scroll-host and page-inset, so the sections only carry the split. -->
    <template v-else>
      <section class="min-w-0 basis-2/5 shrink-0">
        <SettingsHome :active-path="route.path" />
      </section>

      <section class="min-w-0 basis-2/5 shrink-0">
        <component
          :is="settingsDetail"
          v-if="settingsDetail"
          :key="route.path"
        />
        <div
          v-else
          class="flex h-full items-center justify-center"
        >
          <p class="text-body text-dimmed">
            Select a section
          </p>
        </div>
      </section>
    </template>
  </div>
</template>
