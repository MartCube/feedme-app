<script setup lang="ts">
import type { Feed } from '~/assets/types'

// Edit a feed: its name and description, committed together by Save. Deleting
// it is the feed page's own button (feed/Info.vue), not part of this form.
const props = defineProps<{ feed: Feed, back: string }>()

const { updateFeed } = useFeedsStore()

// Local drafts, keyed on the uid so an unrelated store update (a toggle in
// another pane) can't wipe what's being typed.
const name = ref(props.feed.name)
const description = ref(props.feed.description)
watch(() => props.feed.uid, () => {
  name.value = props.feed.name
  description.value = props.feed.description
})

const dirty = computed(() => {
  const n = name.value.trim()
  return n.length > 0 && (n !== props.feed.name || description.value.trim() !== props.feed.description)
})

function save() {
  if (!dirty.value) return
  updateFeed(props.feed.uid, { name: name.value, description: description.value })
  navigateTo(props.back)
}
</script>

<template>
  <div class="flex flex-col">
    <header class="flex items-center justify-between gap-sm">
      <IconButton
        icon="i-ph-caret-left-bold"
        :to="back"
        aria-label="Back to feed"
      />
      <PillButton
        label="Save"
        :disabled="!dirty"
        @click="save"
      />
    </header>

    <section class="mt-lg">
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        Name
      </h3>
      <UInput
        v-model="name"
        class="mt-xs w-full"
        :ui="{ base: 'px-sm py-sm text-body rounded-2xl transition' }"
        @keydown.enter="save"
      />
    </section>

    <section class="mt-lg">
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        Description
      </h3>
      <UInput
        v-model="description"
        class="mt-xs w-full"
        placeholder="What this feed is for"
        :ui="{ base: 'px-sm py-sm text-body rounded-2xl transition' }"
        @keydown.enter="save"
      />
    </section>
  </div>
</template>
