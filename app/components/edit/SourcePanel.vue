<script setup lang="ts">
import type { Feed } from '~/assets/types'

// The edit-source panel. Reached two ways: as a subpage of a folder
// (folderUid set → back caret + swipe-back, destructive action = remove from
// this feed) or directly for a loose source (no folderUid → X close,
// destructive action = delete the source). Edits name + the RSS feed_url only.
const props = defineProps<{ feed: Feed, folderUid?: string }>()

const feedsStore = useFeedsStore()
const { updateFeed } = feedsStore

const closeDrawer = inject(editDrawerCloseKey, () => {})

// Local drafts — committed explicitly by the Save block, not on every keystroke.
// Key the reset on uid, not the feed object, so an unrelated store update
// doesn't wipe in-progress drafts (see FolderPanel).
const name = ref(props.feed.name)
const feedUrl = ref(props.feed.feed_url)
watch(() => props.feed.uid, () => {
  name.value = props.feed.name
  feedUrl.value = props.feed.feed_url
})

const dirty = computed(() => {
  const n = name.value.trim()
  const u = feedUrl.value.trim()
  return (n.length > 0 && n !== props.feed.name) || (u.length > 0 && u !== props.feed.feed_url)
})

function save() {
  if (!dirty.value) return
  updateFeed(props.feed.uid, { name: name.value, feed_url: feedUrl.value })
  closeDrawer()
}

// Swipe right pops back: to the folder panel for a member, or closes to home
// for a loose source (it has no parent). The panel-slide / drawer animates the
// same root div this style binds to.
const backTo = () => (props.folderUid ? `/edit/${props.folderUid}` : '/')
const panel = useTemplateRef('panel')
const { style: swipeStyle } = useSwipeBack(panel, backTo)

// Both destructive paths go through a confirm sheet — the panel only routes.
const deletePath = computed(() => props.folderUid
  ? `/edit/${props.folderUid}/source/${props.feed.uid}/delete`
  : `/edit/${props.feed.uid}/delete`)
</script>

<template>
  <!-- touch-none lets vaul own the touch gesture (drag-to-close). -->
  <div
    ref="panel"
    :style="swipeStyle"
    class="flex h-full touch-none flex-col overflow-y-auto bg-default page-inset"
  >
    <header class="flex items-center justify-between gap-sm">
      <IconButton
        v-if="folderUid"
        icon="i-ph-caret-left-bold"
        :to="`/edit/${folderUid}`"
        aria-label="Back to feed"
      />
      <IconButton
        v-else
        icon="i-ph-x-bold"
        aria-label="Close edit source"
        @click="closeDrawer"
      />
      <PillButton
        label="Save"
        :disabled="!dirty"
        @click="save"
      />
    </header>

    <h1 class="mt-lg truncate text-subtitle tracking-tight text-inset">
      {{ feed.name }}
    </h1>

    <section class="mt-md">
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        Name
      </h3>
      <UInput
        v-model="name"
        class="mt-xs w-full"
        :ui="{ base: 'px-sm py-sm text-body rounded-2xl transition duration-300 ease-out' }"
        @keydown.enter="save"
      />
    </section>

    <section class="mt-lg">
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        RSS URL
      </h3>
      <UInput
        v-model="feedUrl"
        class="mt-xs w-full"
        type="url"
        inputmode="url"
        autocapitalize="off"
        autocorrect="off"
        :ui="{ base: 'px-sm py-sm text-body rounded-2xl transition duration-300 ease-out' }"
        @keydown.enter="save"
      />
    </section>

    <DangerButton
      class="mt-xl"
      :label="folderUid ? 'Remove source from feed' : 'Delete source'"
      :to="deletePath"
    />
  </div>
</template>
