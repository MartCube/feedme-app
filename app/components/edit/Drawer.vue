<script setup lang="ts">
// Hosts the edit-folder / edit-feed bottom sheet. Like the settings and add
// drawers, every /edit/* URL renders the home page component (see the
// pages:extend hook in nuxt.config) so the feed list stays mounted behind the
// sheet. The route-driven panels themselves live in EditPanels; this component
// only opens the sheet on /edit/* and routes home on close.
const route = useRoute()
const open = ref(false)

const wizard = useAddFeedWizard()

const EDIT_NAMES = new Set(['edit', 'edit-feed', 'edit-add', 'edit-add-input', 'edit-delete', 'edit-feed-delete'])
// Every panel inside needs the folder or feed the URL names, and the account's data only
// arrives after hydration — so a cold deep link would otherwise slide up an empty sheet,
// hold it for the length of GET /home, and (for a stale uid) slide it back down still
// empty. Waiting for the store to answer either way is what keeps the sheet honest.
const { loaded, unreachable } = storeToRefs(useFeedsStore())
const onEdit = computed(() =>
  EDIT_NAMES.has(route.name as string) && (loaded.value || unreachable.value),
)

// vaul emits animationEnd(false) for its initial closed state — only a close
// that follows a completed open animation should navigate home.
const hasOpened = ref(false)

watch(onEdit, (on) => {
  open.value = on
})

onMounted(() => {
  // Desktop deep-load guard (see settings/Drawer.vue).
  if (isDesktopNow()) return
  if (onEdit.value) open.value = true
})

provide(editDrawerCloseKey, () => {
  open.value = false
})

function onAnimationEnd(isOpen: boolean) {
  if (isOpen) {
    hasOpened.value = true
  }
  else if (hasOpened.value && onEdit.value) {
    navigateTo('/')
  }
  // Once fully closed, clear any in-progress scoped add so it reopens fresh.
  if (!isOpen) wizard.reset()
}
</script>

<template>
  <UDrawer
    v-model:open="open"
    :handle="false"
    :ui="{
      // overflow-hidden clips the square-cornered panels to the sheet's
      // rounded top corners.
      content: 'mt-0 h-full max-h-full overflow-hidden',
      container: 'grow gap-0 p-0 overflow-hidden',
      body: 'relative overflow-hidden',
    }"
    @animation-end="onAnimationEnd"
  >
    <template #body>
      <EditPanels />
    </template>
  </UDrawer>
</template>
