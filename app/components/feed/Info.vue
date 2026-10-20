<script setup lang="ts">
import type { Feed } from '~/assets/types'

// The feed page: what a feed is and what's in it — its name and description,
// and its sources, each switched on or off for this feed right here. A source
// row opens that source's page. On desktop it fills the post pane whenever
// no post is open; on a phone it's reached by tapping the feed's title.
const props = defineProps<{ uid: string, feed?: Feed, back: string }>()

const feedsStore = useFeedsStore()
const wizard = useAddFeedWizard()

const enabledCount = computed(() => props.feed?.sources.filter(source => source.enabled).length ?? 0)

const { selectedUid, select } = useTapSelection()

const settings = useSettingsStore()

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
</script>

<template>
  <div class="flex flex-col">
    <!-- Back is the phone's way home to the post list; on desktop that list
         is already beside it, so the button keeps its space and hides.
         The actions follow the post's side (Appearance → Post actions): on
         the left the bar swaps, actions left and Back right. -->
    <header
      class="flex items-center justify-between gap-sm"
      :class="settings.actionSide === 'left' && 'flex-row-reverse'"
    >
      <IconButton
        icon="i-ph-caret-left-bold"
        :to="back"
        aria-label="Back to posts"
        class="lg:invisible"
      />
      <!-- Delete is its own button rather than the foot of the edit form:
           the two are different jobs. Edit, the common one, takes the outer
           edge on either side. Delete still goes through its confirm. -->
      <div
        v-if="feed"
        class="flex items-center gap-xs"
        :class="settings.actionSide === 'left' && 'flex-row-reverse'"
      >
        <IconButton
          icon="i-ph-trash-bold"
          :to="`/feed/${uid}/info/delete`"
          aria-label="Delete feed"
        />
        <IconButton
          icon="i-ph-pencil-simple-bold"
          :to="`/feed/${uid}/info/edit`"
          aria-label="Edit feed"
        />
      </div>
    </header>

    <template v-if="feed">
      <h1 class="mt-lg text-title tracking-tight">
        {{ feed.name }}
      </h1>
      <p
        v-if="feed.description"
        class="mt-xs text-body text-muted"
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
  </div>
</template>
