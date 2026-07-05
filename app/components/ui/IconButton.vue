<script setup lang="ts">
const props = withDefaults(defineProps<{
  icon: string
  to?: string
  size?: 'sm' | 'md'
}>(), {
  size: 'md',
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
</script>

<template>
  <UButton
    :to="to"
    variant="ghost"
    color="neutral"
    :ui="{ base: `rounded-full justify-center bg-elevated ${buttonSize} shadow-[0_0_0_1px_var(--color-ink-800),0_2px_6px_-3px_rgba(0,0,0,0.4)] hover:bg-elevated` }"
    @pointerdown="handlePress"
  >
    <UIcon
      :name="icon"
      :class="[iconSize, 'transition-colors duration-300 ease-out', flashing ? 'text-primary' : 'text-default']"
    />
  </UButton>
</template>
