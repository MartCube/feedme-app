<script setup lang="ts">
// The app's one destructive affordance — an elevated card, no icon, that arms
// (blinks red in place) on tap and then routes to its confirm sheet. It never
// mutates anything itself: every delete/remove is confirmed on the next panel.
const props = defineProps<{ label: string, to: string }>()

const armed = ref(false)
// useTimeoutFn stops itself if the panel unmounts mid-blink.
const { start } = useTimeoutFn(() => navigateTo(props.to), 450, { immediate: false })

function arm() {
  if (armed.value) return
  armed.value = true
  start()
}
</script>

<template>
  <button
    type="button"
    class="w-full rounded-2xl bg-elevated py-sm text-body shadow-elevated transition-colors"
    :class="armed ? 'animate-pulse text-error' : 'text-muted'"
    @click="arm"
  >
    {{ label }}
  </button>
</template>
