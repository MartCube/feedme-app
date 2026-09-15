<script setup lang="ts">
import type { Destination } from '~/stores/feeds'

// The four-phase add wizard (type → input → destination → folder) as sliding
// panels. Hosted by the mobile bottom sheet (add/Drawer.vue) and the desktop
// content page; wizard state is global (useAddFeedWizard), so hosts only
// decide what close/done mean — dismiss the sheet vs return to the reader.
// Hosts own resetting the wizard once the flow is dismissed.
// `slide` is the host's call, not the wizard's: the mobile sheet is a single
// pane where motion is the only thing saying which way the flow moved, while
// the desktop content area is a page and its steps just replace each other.
const props = withDefaults(defineProps<{ slide?: boolean }>(), { slide: true })

const emit = defineEmits<{ close: [], done: [] }>()

const wizard = useAddFeedWizard()
const { step, direction } = wizard

// Same push/pop mechanism as the settings drawer (utils/panel-slide.ts), but
// the direction comes from the wizard rather than from path depth: forward =
// push (next phase in from the right), back = pop (previous phase in from the
// left). 'none' holds --panel-duration at 0s, so the steps cut instantly.
const slideVars = computed(() => panelSlideVars(
  !props.slide ? 'none' : direction.value === 'back' ? 'pop' : 'push',
))

// The sheet closes only if the subscribe actually landed — otherwise the step stays up
// with the server's reason on it.
async function onChoose(destination: Destination) {
  if (await wizard.chooseDestination(destination)) emit('done')
}
</script>

<template>
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
        @close="emit('close')"
      />
      <AddSearchStep
        v-else-if="step === 'input'"
        key="input"
        @back="wizard.back"
        @forward="wizard.proceedToDestination"
      />
      <AddDestinationStep
        v-else-if="step === 'destination'"
        key="destination"
        @back="wizard.back"
        @choose="onChoose"
        @new-folder="wizard.goToNewFolder"
      />
      <AddFolderStep
        v-else
        key="folder"
        @back="wizard.back"
        @create="wizard.createFolder"
      />
    </Transition>
  </div>
</template>
