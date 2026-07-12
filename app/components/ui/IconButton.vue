<script setup lang="ts">
const props = withDefaults(defineProps<{
  icon: string
  to?: string
  size?: 'sm' | 'md'
  variant?: 'elevated' | 'quiet'
}>(), {
  size: 'md',
  variant: 'elevated',
})

const flashing = ref(false)

function handlePress() {
  flashing.value = true
  setTimeout(() => {
    flashing.value = false
  }, 250)
}

const buttonSize = computed(() => props.size === 'sm' ? 'size-10' : 'size-12')
const iconSize = computed(() => props.size === 'sm' ? 'size-5' : 'size-6')

// quiet: the circle blends into the page at rest and only lifts to the
// normal elevated look while the press flash runs.
const surface = computed(() => {
  if (props.variant === 'quiet' && !flashing.value) return 'bg-transparent hover:bg-transparent'
  return 'bg-elevated shadow-elevated hover:bg-elevated'
})
</script>

<template>
  <UButton
    :to="to"
    variant="ghost"
    color="neutral"
    :ui="{ base: `rounded-full justify-center ${buttonSize} transition-colors duration-300 ease-out ${surface}` }"
    @pointerdown="handlePress"
  >
    <UIcon
      :name="icon"
      :class="[iconSize, 'transition-colors duration-300 ease-out', flashing ? 'text-primary' : 'text-default']"
    />
  </UButton>
</template>
