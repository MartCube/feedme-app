<script setup lang="ts">
// The attrs go to the button, not the tooltip wrapping it — aria-label,
// aria-expanded, class and listeners all belong on the thing you press.
defineOptions({ inheritAttrs: false })

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

// The label every caller already gives for screen readers doubles as the
// hover tooltip, so a button can't have one without the other.
const attrs = useAttrs()
const label = computed(() => attrs['aria-label'] as string | undefined)

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
  <UTooltip
    :text="label"
    :disabled="!label"
  >
    <UButton
      v-bind="$attrs"
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
  </UTooltip>
</template>
