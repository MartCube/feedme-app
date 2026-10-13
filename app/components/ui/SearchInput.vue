<script setup lang="ts">
const model = defineModel<string>({ default: '' })

const props = withDefaults(defineProps<{
  placeholder?: string
  size?: 'md' | 'lg' | 'xl'
  // Opt-in: adds the focused Paste chip. Search reuse (feed, home) leaves it off.
  paste?: boolean
  // Opt-in: focus on mount (wizard steps). The delay lets the panel-slide
  // finish so the dialog's own focus management doesn't steal it back.
  autofocus?: boolean
  // What the submit arrow does, for screen readers. Every use is a search bar
  // except the login screen's token field.
  submitLabel?: string
  // Off for a live-search field: it re-runs on every keystroke, so there is
  // nothing to submit and the arrow would only compete with the caller's own
  // close button beside it.
  submit?: boolean
}>(), {
  placeholder: '',
  size: 'xl',
  paste: false,
  autofocus: false,
  submitLabel: 'Search',
  submit: true,
})

const emit = defineEmits<{ submit: [] }>()

// The Paste chip shows only while the input is focused and still empty — once
// there's text (typed or pasted) it gives way to the submit arrow.
const focused = ref(false)

// Whether this field can ever put anything in the trailing slot. Nuxt UI
// reserves pe-9 for one whenever the slot is passed at all, and a live-search
// field passes it while rendering neither control — which left the box padded
// 16px on the left and 36px on the right. Deliberately static rather than
// tracking whether a control is showing *right now*: the reserved space has to
// stay put, or the wizard's placeholder would reflow the moment its Paste chip
// appeared on focus.
const canTrail = computed(() => props.submit || props.paste)

// xl is a hero field (the wizard, the login token). Anything smaller is
// embedded in a row beside other controls and takes their height — an
// IconButton's 48px (h-12), so the feed's search lines up with the close
// button beside it instead of sitting 12px short of it.
const box = computed(() => [
  'px-sm text-body rounded-2xl transition',
  props.size === 'xl' ? 'py-sm' : 'h-12 py-xs',
  canTrail.value ? '' : 'pe-sm!',
].join(' '))

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
    <!-- `transition` (not -colors) so the focus ring's box-shadow animates. -->
    <UInput
      v-model="model"
      :placeholder="placeholder"
      :size="size"
      :autofocus="autofocus"
      :autofocus-delay="350"
      class="w-full"
      :ui="{ base: box }"
      @focusin="focused = true"
      @focusout="focused = false"
    >
      <template #trailing>
        <UButton
          v-if="submit && model"
          icon="i-ph-arrow-right-bold"
          color="neutral"
          variant="ghost"
          size="sm"
          type="submit"
          :aria-label="submitLabel"
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
