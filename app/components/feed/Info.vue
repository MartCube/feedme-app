<script setup lang="ts">
import type { Feed } from '~/assets/types'

// The feed page: what a feed is and what's in it — its name and description,
// and its sources, each switched on or off for this feed right here. A source
// row opens that source's page. For Saved, the same slot lists its three
// groups. On desktop it fills the post pane whenever no post is open; on a
// phone it's reached by tapping the feed's title.
const props = defineProps<{ uid: string, feed?: Feed, back: string }>()

const feedsStore = useFeedsStore()
const { savedCounts } = storeToRefs(feedsStore)
const wizard = useAddFeedWizard()

const isSaved = computed(() => props.uid === 'saved' || props.uid.startsWith('saved_'))
const enabledCount = computed(() => props.feed?.sources.filter(source => source.enabled).length ?? 0)

const { selectedUid, select } = useTapSelection()

// On = shown in this feed. Immediate, no Save: a toggle is its own commit.
function setEnabled(sourceUid: string, enabled: boolean) {
  if (props.feed) feedsStore.updateSource(props.feed.uid, sourceUid, { enabled })
}

// The add wizard, already pointed at this feed: it skips "Add to" and commits
// straight from the search step. A fresh flow, so no stale type or results.
function addSource() {
  wizard.reset()
  wizard.target.value = props.uid
  navigateTo('/add')
}

const savedRows = computed(() => [
  {
    uid: 'saved',
    name: 'All saved',
    count: savedCounts.value.bookmarks + savedCounts.value.favorites + savedCounts.value.later,
  },
  ...savedGroups.map(group => ({ uid: group.uid, name: group.name, count: savedCounts.value[group.group] })),
])
</script>

<template>
  <div class="flex flex-col">
    <!-- Back is the phone's way home to the post list; on desktop that list
         is already beside it, so the button keeps its space and hides. -->
    <header class="flex items-center justify-between gap-sm">
      <IconButton
        icon="i-ph-caret-left-bold"
        :to="back"
        aria-label="Back to posts"
        class="lg:invisible"
      />
      <IconButton
        v-if="feed"
        icon="i-ph-pencil-simple-bold"
        :to="`/feed/${uid}/info/edit`"
        aria-label="Edit feed"
      />
    </header>

    <template v-if="feed">
      <h1 class="mt-lg text-title tracking-tight text-inset">
        {{ feed.name }}
      </h1>
      <p
        v-if="feed.description"
        class="mt-xs text-body text-muted text-inset"
      >
        {{ feed.description }}
      </p>

      <section class="mt-lg">
        <h3 class="flex items-baseline gap-xs text-caption font-semibold uppercase tracking-wide text-muted text-inset">
          Sources
          <span
            v-if="feed.sources.length"
            class="font-normal"
          >{{ enabledCount }}/{{ feed.sources.length }}</span>
        </h3>
        <ul
          v-if="feed.sources.length"
          class="mt-xs flex flex-col"
        >
          <!-- Rows span the full width like the inputs and block buttons, and
               carry the inset as real padding, so the name lands at the same x
               as the heading. -->
          <li
            v-for="source in feed.sources"
            :key="source.uid"
            class="flex items-center rounded-2xl pr-sm transition-colors"
            :class="selectedUid === source.uid ? 'bg-elevated shadow-elevated text-primary' : 'hover-accent'"
          >
            <!-- Dimmed by opacity alone, not text-muted: an explicit colour
                 here would beat the row's inherited accent and primary. -->
            <NuxtLink
              :to="`/feed/${uid}/info/source/${source.uid}`"
              class="min-w-0 flex-1 truncate py-sm pl-sm text-body"
              :class="!source.enabled && 'opacity-60'"
              @pointerdown="select(source.uid)"
            >
              {{ source.name }}
            </NuxtLink>
            <!-- Outside the link: interactive-in-interactive is invalid. -->
            <Toggle
              :model-value="source.enabled"
              :aria-label="`${source.enabled ? 'Hide' : 'Show'} ${source.name} in this feed`"
              @update:model-value="setEnabled(source.uid, $event)"
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
          @click="addSource"
        >
          <UIcon
            name="i-ph-plus-bold"
            class="size-5 shrink-0"
          />
          Add source
        </button>
      </section>
    </template>

    <template v-else-if="isSaved">
      <h1 class="mt-lg text-title tracking-tight text-inset">
        Saved
      </h1>
      <ul class="mt-md flex flex-col">
        <li
          v-for="row in savedRows"
          :key="row.uid"
        >
          <NuxtLink
            :to="`/feed/${row.uid}`"
            class="flex items-baseline gap-xs rounded-2xl p-sm text-body transition-colors"
            :class="row.uid === uid || selectedUid === row.uid ? 'bg-elevated shadow-elevated text-primary' : 'hover-accent'"
            @pointerdown="select(row.uid)"
          >
            <span class="truncate">{{ row.name }}</span>
            <span class="text-caption text-muted">{{ row.count }}</span>
          </NuxtLink>
        </li>
      </ul>
    </template>
  </div>
</template>
