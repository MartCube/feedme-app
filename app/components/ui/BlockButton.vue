<script setup lang="ts">
// Full-width action button — the app's block affordance (Save, Delete, …). Soft
// elevated surface with a coloured label per variant, matching the minimal,
// no-loud-fills aesthetic. Disabled dims to a muted, unactionable state.
withDefaults(defineProps<{
  label: string
  icon?: string
  variant?: 'neutral' | 'primary' | 'danger'
  disabled?: boolean
}>(), {
  variant: 'neutral',
  disabled: false,
})

const tone: Record<'neutral' | 'primary' | 'danger', string> = {
  neutral: 'text-default',
  primary: 'text-primary',
  danger: 'text-error',
}
</script>

<template>
  <button
    type="button"
    :disabled="disabled"
    class="flex w-full items-center justify-center gap-sm rounded-2xl bg-elevated py-sm text-body shadow-elevated transition-colors"
    :class="disabled ? 'text-dimmed' : tone[variant]"
  >
    <UIcon
      v-if="icon"
      :name="icon"
      class="size-6 shrink-0"
    />
    {{ label }}
  </button>
</template>
