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

// md steps down to sm on desktop: a pointer doesn't need a fingertip target,
// and the full size outweighed the titles beside it.
const buttonSize = computed(() => props.size === 'sm' ? 'size-10' : 'size-12 lg:size-10')
const iconSize = computed(() => props.size === 'sm' ? 'size-5' : 'size-6 lg:size-5')

// Tooltips are a pointer affordance; a phone has no hover to show them on.
const isDesktop = useIsDesktop()

// quiet: the circle blends into the page at rest and only lifts to the
// normal elevated look while the press flash runs.
const surface = computed(() => {
  if (props.variant === 'quiet' && !flashing.value) return 'bg-transparent hover:bg-transparent'
  return 'bg-elevated shadow-elevated hover:bg-elevated'
})
</script>

<template>
  <!-- Above, not Nuxt UI's default below: below put the label over the
       content the button acts on. The top row is only md (24px) from the
       window edge, so it fits on a 2px offset with no collision padding
       (the label is 15px, app.config.ts) — any more and it flips below.
       Keyed on `to` because Reka takes the trigger element once, on mount: a
       button whose `to` arrives later (Open source, before its post loads)
       swaps <button> for <a> under it, and the tooltip would keep tracking
       the detached button and never close when the pointer leaves. -->
  <UTooltip
    :key="to ? 'link' : 'button'"
    :text="label"
    :disabled="!label || !isDesktop"
    :content="{ side: 'top', sideOffset: 2, collisionPadding: 0 }"
  >
    <UButton
      v-bind="$attrs"
      :to="to"
      variant="ghost"
      color="neutral"
      :ui="{ base: `group/icon rounded-full justify-center ${buttonSize} transition-colors ${surface}` }"
      @pointerdown="handlePress"
    >
      <!-- The icon rests muted, so a row of actions sits quieter than the
         text it acts on. Hover lights it primary, the same cue hover-accent
         gives a list row's label (themes.css) — gated to hover-capable
         pointers for the same reason: :hover sticks after a tap, and the
         flash already covers touch. -->
      <UIcon
        :name="icon"
        :class="[iconSize, 'transition-colors [@media(hover:hover)]:group-hover/icon:text-primary', flashing ? 'text-primary' : 'text-muted']"
      />
    </UButton>
  </UTooltip>
</template>
