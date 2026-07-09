<script setup lang="ts">
const model = defineModel<string>({ default: '' })

withDefaults(defineProps<{
  placeholder?: string
  size?: 'md' | 'lg' | 'xl'
  // Opt-in: adds the focused Paste chip. Search reuse (feed, home) leaves it off.
  paste?: boolean
}>(), {
  placeholder: '',
  size: 'xl',
  paste: false,
})

const emit = defineEmits<{ submit: [] }>()

// The Paste chip shows only while the input is focused and still empty — once
// there's text (typed or pasted) it gives way to the submit arrow.
const focused = ref(false)

// Browsers block silent clipboard reads, so the chip reads on tap (a user
// gesture). mousedown.prevent (on the button) keeps the input focused through
// the click, so focusout doesn't remove the chip before the tap lands.
async function pasteFromClipboard() {
  try {
    const text = await navigator.clipboard.readText()
    if (text) model.value = text
  }
  catch {
    // clipboard blocked/empty — the user can type instead
  }
}
</script>

<template>
  <form @submit.prevent="emit('submit')">
    <UInput
      v-model="model"
      :placeholder="placeholder"
      :size="size"
      class="w-full"
      @focusin="focused = true"
      @focusout="focused = false"
    >
      <template #trailing>
        <UButton
          v-if="model"
          icon="i-ph-arrow-right-bold"
          color="neutral"
          variant="ghost"
          size="sm"
          type="submit"
          aria-label="Search"
        />
        <UButton
          v-else-if="paste && focused"
          label="Paste"
          color="neutral"
          variant="soft"
          size="sm"
          @mousedown.prevent
          @click="pasteFromClipboard"
        />
      </template>
    </UInput>
  </form>
</template>
