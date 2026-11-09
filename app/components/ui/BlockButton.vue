<script setup lang="ts">
// Full-width action button — the app's block affordance (Save, Delete, …). Soft
// elevated surface with a coloured label per variant, matching the minimal,
// no-loud-fills aesthetic. Disabled dims to a muted, unactionable state.
//
// `filled` is the one exception: an accent surface with the theme's inverted
// ink, for the single action a signed-out screen or the error page exists to
// offer (log in, sign up, back to your feeds). Nowhere inside the app.
type Variant = 'neutral' | 'primary' | 'danger' | 'filled'

const props = withDefaults(defineProps<{
  label: string
  icon?: string
  variant?: Variant
  type?: 'button' | 'submit'
  disabled?: boolean
}>(), {
  variant: 'neutral',
  type: 'button',
  disabled: false,
})

// The elevated variants share one hover/press: the surface steps to bg-muted
// (block-feedback, themes.css) — the label is already coloured, so it can't
// be the cue. `filled` keeps its own look; it lives outside the app.
const tone: Record<Variant, string> = {
  neutral: 'bg-elevated text-default shadow-elevated block-feedback',
  primary: 'bg-elevated text-primary shadow-elevated block-feedback',
  danger: 'bg-elevated text-error shadow-elevated block-feedback',
  filled: 'bg-primary text-inverted font-semibold',
}

// In script, not the template: here `props.variant` is typed with its default
// applied, while some editors' Vue tooling reads the template's `variant` as
// possibly undefined and flags the index.
const toneClass = computed(() =>
  props.disabled ? 'bg-elevated text-dimmed shadow-elevated' : tone[props.variant],
)
</script>

<template>
  <button
    :type="type"
    :disabled="disabled"
    class="flex w-full items-center justify-center gap-sm rounded-2xl py-sm text-body transition"
    :class="toneClass"
  >
    <UIcon
      v-if="icon"
      :name="icon"
      class="size-6 shrink-0"
    />
    {{ label }}
  </button>
</template>
