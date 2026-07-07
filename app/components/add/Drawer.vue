<script setup lang="ts">
// Hosts the add-feed wizard bottom sheet. Like the settings drawer, the /add
// URL renders the home page component (see the pages:extend hook in
// nuxt.config) so the feed list stays mounted behind the sheet. This component
// opens the drawer on /add, drives the three-phase wizard (type → input →
// destination) via useAddFeedWizard, routes home on close, and resets the
// wizard once the sheet has fully closed.
import type { Destination } from '~/stores/feeds'

const route = useRoute()
const open = ref(false)

const onAdd = computed(() => route.path === '/add')

// vaul emits animationEnd(false) for its initial closed state — only a close
// that follows a completed open animation should navigate home.
const hasOpened = ref(false)

const wizard = useAddFeedWizard()
const { step, direction } = wizard

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

function onChoose(destination: Destination) {
  wizard.chooseDestination(destination)
  close()
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
      body: 'relative overflow-hidden',
    }"
    @animation-end="onAnimationEnd"
  >
    <template #body>
      <!-- touch-none lets vaul own the drag-to-close gesture; revisit once the
           results list needs real touch scrolling. -->
      <div class="h-full touch-none overflow-y-auto bg-default px-8 pt-6 pb-12">
        <div class="flex justify-end">
          <IconButton
            icon="i-ph-x-bold"
            aria-label="Close add feed"
            @click="close"
          />
        </div>

        <Transition
          :name="direction === 'forward' ? 'wizard-forward' : 'wizard-back'"
          mode="out-in"
        >
          <AddTypeStep
            v-if="step === 'type'"
            key="type"
            class="mt-4"
            @select="wizard.selectType"
          />
          <AddSearchStep
            v-else-if="step === 'input'"
            key="input"
            class="mt-4"
            @back="wizard.back"
            @pick="wizard.pickFeed"
          />
          <AddDestinationStep
            v-else
            key="destination"
            class="mt-4"
            @back="wizard.back"
            @choose="onChoose"
          />
        </Transition>
      </div>
    </template>
  </UDrawer>
</template>
