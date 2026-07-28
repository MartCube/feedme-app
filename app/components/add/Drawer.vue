<script setup lang="ts">
// Hosts the add-feed wizard bottom sheet. Like the settings drawer, the /add
// URL renders the home page component (see the pages:extend hook in
// nuxt.config) so the feed list stays mounted behind the sheet. This component
// opens the drawer on /add, routes home on close, and resets the wizard once
// the sheet has fully closed; the wizard panels themselves live in AddSteps.
const route = useRoute()
const open = ref(false)

const onAdd = computed(() => route.path === '/add')

// vaul emits animationEnd(false) for its initial closed state — only a close
// that follows a completed open animation should navigate home.
const hasOpened = ref(false)

const wizard = useAddFeedWizard()

watch(onAdd, (on) => {
  open.value = on
})

onMounted(() => {
  if (onAdd.value) {
    open.value = true
  }
})

function close() {
  open.value = false
}

function onAnimationEnd(isOpen: boolean) {
  if (isOpen) {
    hasOpened.value = true
  }
  else if (hasOpened.value && onAdd.value) {
    navigateTo('/')
  }
  // Once the sheet is fully closed, clear wizard state so it reopens fresh.
  if (!isOpen) {
    wizard.reset()
  }
}
</script>

<template>
  <UDrawer
    v-model:open="open"
    :handle="false"
    :ui="{
      // overflow-hidden clips the panel to the sheet's rounded top corners.
      content: 'mt-0 h-full max-h-full overflow-hidden',
      container: 'grow gap-0 p-0 overflow-hidden',
      body: 'overflow-hidden',
    }"
    @animation-end="onAnimationEnd"
  >
    <template #body>
      <AddSteps
        @close="close"
        @done="close"
      />
    </template>
  </UDrawer>
</template>
