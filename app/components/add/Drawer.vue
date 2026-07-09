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

// Same push/pop mechanism as the settings drawer: a FIXED panel-slide
// transition whose direction rides on --panel-* variables (see
// .slide-panels in transitions.css). forward = push (next phase in from the
// right), back = pop (previous phase back in from the left).
const slideVars = computed(() => {
  if (direction.value === 'back') {
    return { '--panel-enter-from': '-25%', '--panel-leave-to': '100%', '--panel-leave-z': '1' }
  }
  return { '--panel-enter-from': '100%', '--panel-leave-to': '-25%', '--panel-enter-z': '1' }
})

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
      body: 'overflow-hidden',
    }"
    @animation-end="onAnimationEnd"
  >
    <template #body>
      <!-- Full-bleed panels that slide as whole slabs, exactly like the
           settings drawer. Each step owns its scroll/padding/background. -->
      <div
        class="slide-panels h-full"
        :style="slideVars"
      >
        <Transition name="panel-slide">
          <AddTypeStep
            v-if="step === 'type'"
            key="type"
            @select="wizard.selectType"
            @close="close"
          />
          <AddSearchStep
            v-else-if="step === 'input'"
            key="input"
            @back="wizard.back"
            @pick="wizard.pickFeed"
          />
          <AddDestinationStep
            v-else
            key="destination"
            @back="wizard.back"
            @choose="onChoose"
          />
        </Transition>
      </div>
    </template>
  </UDrawer>
</template>
