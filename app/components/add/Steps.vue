<script setup lang="ts">
import type { Destination } from '~/stores/feeds'

// The four-phase add wizard (type → input → destination → folder) as sliding
// panels. Hosted by the mobile bottom sheet (add/Drawer.vue) and the desktop
// content page; wizard state is global (useAddFeedWizard), so hosts only
// decide what close/done mean — dismiss the sheet vs return to the reader.
// Hosts own resetting the wizard once the flow is dismissed.
const emit = defineEmits<{ close: [], done: [] }>()

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
