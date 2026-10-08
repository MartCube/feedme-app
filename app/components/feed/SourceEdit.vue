<script setup lang="ts">
import type { Feed, Source } from '~/assets/types'

// One source inside one feed: your name for it here, and its link. A blank
// name falls back to the source's own title. Changing the link swaps which
// source this is — it's fetched first, so a URL that isn't a feed is refused
// and nothing changes. Removing it from the feed goes through a confirm.
const props = defineProps<{ feed: Feed, source: Source, back: string }>()

const feedsStore = useFeedsStore()

// The rename draft starts blank when there is none, so the placeholder can
// show the title it falls back to.
const name = ref(props.source.name === props.source.title ? '' : props.source.name)
const link = ref(props.source.feed_url)
const error = ref<string | null>(null)
const saving = ref(false)
watch(() => props.source.uid, () => {
  name.value = props.source.name === props.source.title ? '' : props.source.name
  link.value = props.source.feed_url
  error.value = null
})

const renamed = computed(() => (name.value.trim() || props.source.title) !== props.source.name)
const relinked = computed(() => link.value.trim() !== '' && link.value.trim() !== props.source.feed_url)
const dirty = computed(() => renamed.value || relinked.value)

async function save() {
  if (!dirty.value || saving.value) return
  if (renamed.value) feedsStore.updateSource(props.feed.uid, props.source.uid, { name: name.value })
  if (relinked.value) {
    saving.value = true
    error.value = null
    try {
      await feedsStore.relinkSource(props.feed.uid, props.source.uid, link.value.trim())
    }
    catch (failure) {
      error.value = (failure as { data?: { detail?: string } })?.data?.detail || 'Couldn\'t change the link.'
      return
    }
    finally {
      saving.value = false
    }
  }
  // Back to the feed page, not this one: a new link is a different source,
  // with a different uid in the path.
  navigateTo(`/feed/${props.feed.uid}/info`)
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
        :label="saving ? 'Saving…' : 'Save'"
        :disabled="!dirty || saving"
        @click="save"
      />
    </header>

    <h1 class="mt-lg truncate text-subtitle tracking-tight text-inset">
      {{ source.name }}
    </h1>
    <p class="mt-2xs text-caption text-muted text-inset">
      In {{ feed.name }}
    </p>

    <section class="mt-lg">
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        Name
      </h3>
      <UInput
        v-model="name"
        class="mt-xs w-full"
        :placeholder="source.title"
        :ui="{ base: 'px-sm py-sm text-body rounded-2xl transition' }"
        @keydown.enter="save"
      />
    </section>

    <section class="mt-lg">
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        Link
      </h3>
      <UInput
        v-model="link"
        class="mt-xs w-full"
        type="url"
        :ui="{ base: 'px-sm py-sm text-body rounded-2xl transition' }"
        @keydown.enter="save"
      />
      <p
        v-if="error"
        class="mt-xs text-caption text-error text-inset"
      >
        {{ error }}
      </p>
    </section>

    <DangerButton
      class="mt-xl"
      label="Remove from this feed"
      :to="`/feed/${feed.uid}/info/source/${source.uid}/remove`"
    />
  </div>
</template>
