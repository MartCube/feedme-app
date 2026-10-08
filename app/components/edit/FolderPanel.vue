<script setup lang="ts">
import type { Folder } from '~/assets/types'

// The edit-folder base panel: rename the folder, toggle its member feeds
// on/off (per-folder mute), add a feed straight into it, drill into a member,
// or delete the folder.
// `activeUid` is the desktop master–detail selection: the member whose panel
// is open in the detail pane keeps the elevated row persistently. The mobile
// sheet passes none and relies on the tap flash alone.
const props = defineProps<{ folder: Folder, activeUid?: string }>()

const feedsStore = useFeedsStore()
const { memberFeeds, renameFolder, setMutedFeeds } = feedsStore
const wizard = useAddFeedWizard()

const closeDrawer = inject(editDrawerCloseKey, () => {})
const { selectedUid, select } = useTapSelection()

const members = computed(() => memberFeeds(props.folder))

// Mobile tap flash OR persistent desktop selection — same rule and treatment
// as the feed list's rows.
function isActive(feedUid: string) {
  return selectedUid.value === feedUid || props.activeUid === feedUid
}

// Local drafts so edits are explicit — the name and the per-feed mutes are
// both staged here and committed together by the Save pill, never on the
// keystroke or the toggle. Key the reset on uid, not the folder object, so an
// unrelated store update can't wipe an in-progress draft.
const name = ref(props.folder.name)
const muted = ref([...props.folder.muted_feed_uids])
watch(() => props.folder.uid, () => {
  name.value = props.folder.name
  muted.value = [...props.folder.muted_feed_uids]
})

const renamed = computed(() => {
  const trimmed = name.value.trim()
  return trimmed.length > 0 && trimmed !== props.folder.name
})

// Order-insensitive: only membership of the muted set matters.
const remuted = computed(() => {
  const committed = props.folder.muted_feed_uids
  return muted.value.length !== committed.length
    || muted.value.some(uid => !committed.includes(uid))
})

const dirty = computed(() => renamed.value || remuted.value)

function save() {
  if (!dirty.value) return
  if (renamed.value) renameFolder(props.folder.uid, name.value)
  if (remuted.value) setMutedFeeds(props.folder.uid, muted.value)
  closeDrawer()
}

function isMuted(feedUid: string) {
  return muted.value.includes(feedUid)
}

function toggleMute(feedUid: string) {
  muted.value = muted.value.includes(feedUid)
    ? muted.value.filter(u => u !== feedUid)
    : [...muted.value, feedUid]
}

// Enter the scoped add flow fresh (no stale type/results from a prior add).
function startAdd() {
  wizard.reset()
  navigateTo(`/edit/${props.folder.uid}/add`)
}

const deletePath = computed(() => `/edit/${props.folder.uid}/delete`)
</script>

<template>
  <!-- touch-none lets vaul own the drag-to-close gesture. -->
  <div class="flex h-full touch-none flex-col scroll-host bg-default page-inset">
    <header class="flex items-center justify-between gap-sm">
      <IconButton
        icon="i-ph-x-bold"
        aria-label="Close edit folder"
        @click="closeDrawer"
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
        Feeds
      </h3>
      <ul
        v-if="members.length"
        class="mt-xs flex flex-col"
      >
        <!-- Rows span the full width like the inputs and block buttons, and
             carry the inset as real padding (pl-sm on the link, pr-sm here) —
             so the row name lands at the same x as input text and the 'Feeds'
             heading, and the selected card matches the inputs exactly. -->
        <li
          v-for="feed in members"
          :key="feed.uid"
          class="flex items-center rounded-2xl pr-sm transition-colors"
          :class="isActive(feed.uid) ? 'bg-elevated shadow-elevated text-primary' : 'hover-accent'"
        >
          <!-- Dimmed by opacity alone, not text-muted: an explicit colour here
               would beat the row's inherited accent and primary. -->
          <NuxtLink
            :to="`/edit/${folder.uid}/feed/${feed.uid}`"
            class="min-w-0 flex-1 truncate py-sm pl-sm text-body"
            :class="isMuted(feed.uid) && 'opacity-60'"
            @pointerdown="select(feed.uid)"
          >
            {{ feed.name }}
          </NuxtLink>
          <!-- On = not muted. Sits outside the link (interactive-in-interactive
               is invalid). -->
          <Toggle
            :model-value="!isMuted(feed.uid)"
            :aria-label="`${isMuted(feed.uid) ? 'Enable' : 'Mute'} ${feed.name} in this folder`"
            @update:model-value="toggleMute(feed.uid)"
          />
        </li>
      </ul>
      <p
        v-else
        class="mt-xs text-caption text-muted text-inset"
      >
        No feeds yet.
      </p>

      <!-- Dashed ghost row, full width like the rows above it. -->
      <button
        type="button"
        class="mt-xs flex w-full items-center justify-center gap-xs rounded-2xl border border-dashed border-default py-sm text-body text-muted transition-colors"
        @click="startAdd"
      >
        <UIcon
          name="i-ph-plus-bold"
          class="size-5 shrink-0"
        />
        Add feed
      </button>
    </section>

    <DangerButton
      class="mt-xl"
      label="Delete folder"
      :to="deletePath"
    />
  </div>
</template>
