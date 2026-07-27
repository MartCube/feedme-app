<script setup lang="ts">
import type { Folder } from '~/assets/types'

// The edit-feed (folder) base panel: rename the folder, toggle its member
// sources on/off (per-folder mute), add a source straight into it, drill into
// a source, or delete the folder.
const props = defineProps<{ folder: Folder }>()

const feedsStore = useFeedsStore()
const { memberFeeds, renameFolder, toggleMute } = feedsStore
const wizard = useAddFeedWizard()

const closeDrawer = inject(editDrawerCloseKey, () => {})
const { selectedUid, select } = useTapSelection()

const sources = computed(() => memberFeeds(props.folder))

// Local draft so name edits are explicit — committed by the Save pill, not on
// every keystroke. Reset if the folder changes underneath.
// Key the reset on uid, not the folder object: muting a source replaces the
// folder object (immutable update) but must NOT wipe an in-progress name draft.
const name = ref(props.folder.name)
watch(() => props.folder.uid, () => (name.value = props.folder.name))

const dirty = computed(() => {
  const trimmed = name.value.trim()
  return trimmed.length > 0 && trimmed !== props.folder.name
})

function save() {
  if (!dirty.value) return
  renameFolder(props.folder.uid, name.value)
}

function isMuted(feedUid: string) {
  return props.folder.muted_feed_uids.includes(feedUid)
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
  <div class="flex h-full touch-none flex-col overflow-y-auto bg-default page-inset">
    <header class="flex items-center justify-between gap-sm">
      <IconButton
        icon="i-ph-x-bold"
        aria-label="Close edit feed"
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
        :ui="{ base: 'px-sm py-sm text-body rounded-2xl transition duration-300 ease-out' }"
        @keydown.enter="save"
      />
    </section>

    <section class="mt-lg">
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        Sources
      </h3>
      <ul
        v-if="sources.length"
        class="mt-xs flex flex-col"
      >
        <!-- Rows span the full width like the inputs and block buttons, and
             carry the inset as real padding (pl-sm on the link, pr-sm here) —
             so the row name lands at the same x as input text and the 'Sources'
             heading, and the selected card matches the inputs exactly. -->
        <li
          v-for="feed in sources"
          :key="feed.uid"
          class="flex items-center rounded-2xl pr-sm transition-colors"
          :class="selectedUid === feed.uid && 'bg-elevated shadow-elevated'"
        >
          <NuxtLink
            :to="`/edit/${folder.uid}/source/${feed.uid}`"
            class="min-w-0 flex-1 truncate py-sm pl-sm text-body"
            :class="isMuted(feed.uid) && 'text-muted opacity-60'"
            @pointerdown="select(feed.uid)"
          >
            {{ feed.name }}
          </NuxtLink>
          <!-- On = not muted. Sits outside the link (interactive-in-interactive
               is invalid). -->
          <Toggle
            :model-value="!isMuted(feed.uid)"
            :aria-label="`${isMuted(feed.uid) ? 'Enable' : 'Mute'} ${feed.name} in this feed`"
            @update:model-value="toggleMute(folder.uid, feed.uid)"
          />
        </li>
      </ul>
      <p
        v-else
        class="mt-xs text-caption text-muted text-inset"
      >
        No sources yet.
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
        Add source
      </button>
    </section>

    <DangerButton
      class="mt-xl"
      label="Delete feed"
      :to="deletePath"
    />
  </div>
</template>
