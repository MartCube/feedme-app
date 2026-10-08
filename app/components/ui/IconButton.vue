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
    :ui="{ base: `group/icon rounded-full justify-center ${buttonSize} transition-colors ${surface}` }"
    @pointerdown="handlePress"
  >
    <!-- Hover lights the icon primary, the same cue hover-accent gives a list
         row's label (themes.css) — gated to hover-capable pointers for the
         same reason: :hover sticks after a tap, and the flash already covers
         touch. -->
    <UIcon
      :name="icon"
      :class="[iconSize, 'transition-colors [@media(hover:hover)]:group-hover/icon:text-primary', flashing ? 'text-primary' : 'text-default']"
    />
  </UButton>
</template>
