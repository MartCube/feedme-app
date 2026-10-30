<script setup lang="ts">
// Full-width action button — the app's block affordance (Save, Delete, …). Soft
// elevated surface with a coloured label per variant, matching the minimal,
// no-loud-fills aesthetic. Disabled dims to a muted, unactionable state.
//
// `filled` is the one exception: an accent surface with the theme's inverted
// ink, for the single action a signed-out screen or the error page exists to
// offer (log in, sign up, back to your feeds). Nowhere inside the app.
type Variant = 'neutral' | 'primary' | 'danger' | 'filled'

withDefaults(defineProps<{
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

const tone: Record<Variant, string> = {
  neutral: 'bg-elevated text-default shadow-elevated',
  primary: 'bg-elevated text-primary shadow-elevated',
  danger: 'bg-elevated text-error shadow-elevated',
  filled: 'bg-primary text-inverted font-semibold',
}
</script>

<template>
  <button
    :type="type"
    :disabled="disabled"
    class="flex w-full items-center justify-center gap-sm rounded-2xl py-sm text-body transition-colors"
    :class="disabled ? 'bg-elevated text-dimmed shadow-elevated' : tone[variant]"
  >
    <UIcon
      v-if="icon"
      :name="icon"
      class="size-6 shrink-0"
    />
    {{ label }}
  </button>
</template>
