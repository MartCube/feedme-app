<script setup lang="ts">
// The four-phase add wizard (type → input → destination → new feed) as sliding
// panels. Hosted by the mobile bottom sheet (add/Drawer.vue) and the desktop
// content page; wizard state is global (useAddFeedWizard), so hosts only
// decide what close/done mean — dismiss the sheet vs return to the reader.
// Hosts own resetting the wizard once the flow is dismissed.
// `slide` is the host's call, not the wizard's: the mobile sheet is a single
// pane where motion is the only thing saying which way the flow moved, while
// on desktop the wizard fills the post pane and its steps just replace each
// other.
const props = withDefaults(defineProps<{ slide?: boolean }>(), { slide: true })

// `done` carries the feed the add landed in — the hosts open it.
const emit = defineEmits<{ close: [], done: [feedUid: string] }>()

const wizard = useAddFeedWizard()
const { step, direction } = wizard

// Same push/pop mechanism as the settings drawer (utils/panel-slide.ts), but
// the direction comes from the wizard rather than from path depth: forward =
// push (next phase in from the right), back = pop (previous phase in from the
// left). 'none' holds --panel-duration at 0s, so the steps cut instantly.
const slideVars = computed(() => panelSlideVars(
  !props.slide ? 'none' : direction.value === 'back' ? 'pop' : 'push',
))

// The sheet closes only if the add actually landed — otherwise the step stays
// up with the server's reason on it.
async function onChoose(feedUid: string) {
  const landed = await wizard.addTo(feedUid)
  if (landed) emit('done', landed)
}

async function onCreate(name: string) {
  const landed = await wizard.addToNewFeed(name)
  if (landed) emit('done', landed)
}

// Opened from a feed page, the feed is already chosen: the search step's
// forward commits into it and the destination step is skipped.
function onForward() {
  if (wizard.target.value) onChoose(wizard.target.value)
  else wizard.proceedToDestination()
}
</script>

<template>
  <!-- Full-bleed panels that slide as whole slabs, exactly like the
       settings drawer. Each step owns its scroll/padding/background, and
       holds its children to the form measure (*:max-w-reading) so the
       scroll — and its scrollbar — still spans the whole desktop pane. -->
  <div
    class="slide-panels h-full"
    :style="slideVars"
  >
    <!-- css off when not sliding (the desktop page): the steps swap in one
         frame with no leave-active phase, so there is nothing to glitch. -->
    <Transition
      name="panel-slide"
      :css="props.slide"
    >
      <AddTypeStep
        v-if="step === 'type'"
        key="type"
        @select="wizard.selectType"
        @close="emit('close')"
      />
      <AddSearchStep
        v-else-if="step === 'input'"
        key="input"
        @back="wizard.back"
        @close="emit('close')"
        @forward="onForward"
      />
      <AddDestinationStep
        v-else-if="step === 'destination'"
        key="destination"
        @back="wizard.back"
        @close="emit('close')"
        @choose="onChoose"
        @new-feed="wizard.goToNewFeed"
      />
      <AddNewFeedStep
        v-else
        key="new-feed"
        @back="wizard.back"
        @close="emit('close')"
        @create="onCreate"
      />
    </Transition>
  </div>
</template>
