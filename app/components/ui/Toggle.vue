<script setup lang="ts">
// On/off switch, sized for touch. Stays on-theme: an elevated track (never a
// white fill) with a knob that turns primary when on and sits muted when off —
// position + colour both carry the state. Controlled via v-model.
const model = defineModel<boolean>({ default: false })
</script>

<template>
  <button
    type="button"
    role="switch"
    :aria-checked="model"
    class="relative inline-flex h-8 w-14 shrink-0 items-center rounded-full bg-elevated shadow-elevated transition-colors"
    @click="model = !model"
  >
    <span
      class="absolute left-1 size-6 rounded-full shadow-sm transition-all duration-200 ease-out"
      :class="model ? 'translate-x-6 bg-primary' : 'translate-x-0 bg-muted'"
    />
  </button>
</template>
