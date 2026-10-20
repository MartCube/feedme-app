<script setup lang="ts">
// The confirm standing in front of every destructive action on the feed page —
// delete a feed, remove a source from it. Purely presentational: InfoPanels.vue
// supplies the copy and owns the store mutation.
const props = defineProps<{
  // Doubles as the heading and the confirm button's label.
  action: string
  verb: string
  subject: string
  // Set when the subject is being removed *from* something, not deleted.
  context?: string
  note: string
  backTo: string
}>()

defineEmits<{ confirm: [] }>()

// Everything after the bolded subject, so the question stays one text node and
// Vue doesn't condense away the space before it.
const tail = computed(() => (props.context ? ` from ${props.context}?` : '?'))
</script>

<template>
  <div class="flex flex-col">
    <IconButton
      icon="i-ph-caret-left-bold"
      :to="backTo"
      aria-label="Cancel"
    />

    <h1 class="mt-lg text-subtitle tracking-tight">
      {{ action }}
    </h1>

    <p class="mt-md text-body">
      {{ verb }} <span class="font-semibold">{{ subject }}</span>{{ tail }}
    </p>
    <p class="mt-xs text-caption text-muted">
      {{ note }}
    </p>

    <div class="mt-xl flex flex-col gap-sm">
      <BlockButton
        :label="action"
        variant="danger"
        @click="$emit('confirm')"
      />
      <BlockButton
        label="Cancel"
        variant="neutral"
        @click="navigateTo(backTo)"
      />
    </div>
  </div>
</template>
