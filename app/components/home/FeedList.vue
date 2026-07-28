<script setup lang="ts">
// The home feed list: Home row → pinned Saved group → folders → loose feeds.
// Rendered by the mobile home page and, on desktop, by the sidebar — so all
// list state (tap flash, long-press edit, options sheet) lives here, not in
// the page. `activeUid` is the desktop master–detail selection: the open
// feed's row keeps the elevated treatment persistently.
// No top margin of its own — the gap above the Home row is page context (the
// mobile page clears its navbar; the desktop sidebar starts flush).
const props = defineProps<{ activeUid?: string | null }>()

const feedsStore = useFeedsStore()
const { folders, looseFeeds } = storeToRefs(feedsStore)
const { memberFeeds, isExpanded, toggleFolder } = feedsStore

const settings = useSettingsStore()
// Cards mode: only top-level rows (Saved, folders, loose feeds) keep the
// elevated surface permanently — their tap flash merges into it (the icon
// accent flash stays the cue). Member rows stay plain and keep the flash.
const isCards = computed(() => settings.feedListStyle === 'cards')

const { selectedUid, select } = useTapSelection()

// Mobile tap flash OR persistent desktop selection.
function isActive(uid: string) {
  return selectedUid.value === uid || props.activeUid === uid
}

// Long-press a folder or loose-source row to edit it (mobile); the same edit
// route is reached on desktop via a hover-revealed 3-dot on the row.
const editPress = useLongPress(uid => navigateTo(`/edit/${uid}`))

const optionsOpen = ref(false)

// Tap feedback for the plain icon triggers (chevrons, 3-dot), same primary
// flash as IconButton.
const flashingIcon = ref<string | null>(null)
let flashTimer: ReturnType<typeof setTimeout> | undefined

function flashIcon(uid: string) {
  clearTimeout(flashTimer)
  flashingIcon.value = uid
  flashTimer = setTimeout(() => {
    flashingIcon.value = null
  }, 250)
}

onScopeDispose(() => clearTimeout(flashTimer))
</script>

<template>
  <div class="flex flex-col">
    <!-- Home is a list row like the rest (same surface, flash, cards
         treatment), linking to the merged all-feeds read. Its extras: the
         "All feeds" caption and the 3-dot options trigger sitting where the
         folder rows keep their chevron. -->
    <div
      class="-mx-sm flex items-center rounded-2xl transition-colors"
      :class="(isCards || isActive('all')) && 'bg-elevated shadow-elevated'"
    >
      <NuxtLink
        to="/feed/all"
        class="min-w-0 flex-1 py-sm pl-sm"
        @pointerdown="select('all')"
      >
        <h1 class="text-title tracking-tight">
          Home
        </h1>
        <p class="text-caption text-muted">
          All feeds
        </p>
      </NuxtLink>
      <button
        type="button"
        class="mr-sm flex size-12 shrink-0 items-center justify-center rounded-full"
        aria-label="Feed options"
        @pointerdown="flashIcon('options')"
        @click="optionsOpen = true"
      >
        <UIcon
          name="i-ph-dots-three-bold"
          class="size-6 transition-colors duration-300 ease-out"
          :class="flashingIcon === 'options' ? 'text-primary' : 'text-default'"
        />
      </button>
    </div>

    <!-- Cards-mode spacing is per-row margins, not a ul gap: md between
         top-level cards, xs for the plain member rows inside a dropdown. -->
    <ul
      v-auto-animate
      class="mt-md flex flex-col"
    >
      <!-- Pinned Saved group: same split row as folders (link + chevron), but
           its members are the fixed saved groups, not store feeds. Expansion
           reuses expandedFolderUids under the literal 'saved' uid. -->
      <li
        class="-mx-sm flex items-center rounded-2xl transition-colors"
        :class="isCards ? 'bg-elevated shadow-elevated mt-md first:mt-0' : isActive('saved') && 'bg-elevated shadow-elevated'"
      >
        <NuxtLink
          to="/feed/saved"
          class="flex min-w-0 flex-1 items-baseline gap-xs py-sm pl-sm"
          @pointerdown="select('saved')"
        >
          <span class="truncate text-body">Saved</span>
        </NuxtLink>
        <button
          type="button"
          class="mr-sm flex size-12 shrink-0 items-center justify-center rounded-full transition-transform duration-200"
          :class="isExpanded('saved') && 'rotate-90'"
          :aria-expanded="isExpanded('saved')"
          :aria-label="isExpanded('saved') ? 'Collapse Saved' : 'Expand Saved'"
          @pointerdown="flashIcon('saved')"
          @click="toggleFolder('saved')"
        >
          <UIcon
            name="i-ph-caret-right-bold"
            class="size-6 transition-colors duration-300 ease-out"
            :class="flashingIcon === 'saved' ? 'text-primary' : 'text-default'"
          />
        </button>
      </li>
      <template v-if="isExpanded('saved')">
        <li
          v-for="group in savedGroups"
          :key="group.uid"
          :class="isCards && 'mt-xs'"
        >
          <NuxtLink
            :to="`/feed/${group.uid}`"
            class="-mr-sm block truncate rounded-2xl py-sm pl-md pr-sm text-body transition-colors"
            :class="isActive(group.uid) && 'bg-elevated shadow-elevated'"
            @pointerdown="select(group.uid)"
          >
            {{ group.name }}
          </NuxtLink>
        </li>
      </template>

      <template
        v-for="folder in folders"
        :key="folder.uid"
      >
        <!-- The li is the card surface so link + chevron read as one; the
             chevron can't nest inside the NuxtLink (button-in-anchor is
             invalid HTML). select() stays on the link so chevron taps toggle
             without flashing the row. -->
        <li
          class="group -mx-sm flex items-center rounded-2xl transition-colors"
          :class="isCards ? 'bg-elevated shadow-elevated mt-md first:mt-0' : isActive(folder.uid) && 'bg-elevated shadow-elevated'"
        >
          <NuxtLink
            :to="`/feed/${folder.uid}`"
            class="flex min-w-0 flex-1 items-baseline gap-xs py-sm pl-sm"
            @pointerdown="select(folder.uid); editPress.start(folder.uid, $event)"
            @pointermove="editPress.move"
            @pointerup="editPress.cancel"
            @pointercancel="editPress.cancel"
            @click.capture="editPress.onClick(folder.uid, $event)"
          >
            <span class="truncate text-body">{{ folder.name }}</span>
            <span class="text-caption text-muted">{{ folder.feed_uids.length }}</span>
          </NuxtLink>
          <!-- Desktop only (hover-capable pointers): a quiet 3-dot appears on
               row hover to open the edit drawer; hidden on touch, where the
               long-press above is the entry. -->
          <IconButton
            icon="i-ph-dots-three-bold"
            :to="`/edit/${folder.uid}`"
            variant="quiet"
            size="sm"
            :aria-label="`Edit ${folder.name}`"
            class="hidden shrink-0 [@media(hover:hover)]:group-hover:inline-flex"
          />
          <!-- IconButton dimensions (size-12 circle, size-6 icon); mr-sm pulls
               its right edge back to the content edge so its center shares the
               navbar buttons' vertical axis despite the li's -mx-sm bleed. -->
          <button
            type="button"
            class="mr-sm flex size-12 shrink-0 items-center justify-center rounded-full transition-transform duration-200"
            :class="isExpanded(folder.uid) && 'rotate-90'"
            :aria-expanded="isExpanded(folder.uid)"
            :aria-label="isExpanded(folder.uid) ? `Collapse ${folder.name}` : `Expand ${folder.name}`"
            @pointerdown="flashIcon(folder.uid)"
            @click="toggleFolder(folder.uid)"
          >
            <UIcon
              name="i-ph-caret-right-bold"
              class="size-6 transition-colors duration-300 ease-out"
              :class="flashingIcon === folder.uid ? 'text-primary' : 'text-default'"
            />
          </button>
        </li>
        <template v-if="isExpanded(folder.uid)">
          <li
            v-for="feed in memberFeeds(folder)"
            :key="`${folder.uid}_${feed.uid}`"
            :class="isCards && 'mt-xs'"
          >
            <NuxtLink
              :to="`/feed/${feed.uid}`"
              class="-mr-sm block truncate rounded-2xl py-sm pl-md pr-sm text-body transition-colors"
              :class="[
                folder.muted_feed_uids.includes(feed.uid) && 'text-muted opacity-60',
                isActive(feed.uid) && 'bg-elevated shadow-elevated',
              ]"
              @pointerdown="select(feed.uid)"
            >
              {{ feed.name }}
            </NuxtLink>
          </li>
        </template>
      </template>

      <li
        v-for="feed in looseFeeds"
        :key="feed.uid"
        class="group -mx-sm flex items-center rounded-2xl transition-colors"
        :class="isCards ? 'bg-elevated shadow-elevated mt-md first:mt-0' : isActive(feed.uid) && 'bg-elevated shadow-elevated'"
      >
        <NuxtLink
          :to="`/feed/${feed.uid}`"
          class="min-w-0 flex-1 truncate px-sm py-sm text-body"
          @pointerdown="select(feed.uid); editPress.start(feed.uid, $event)"
          @pointermove="editPress.move"
          @pointerup="editPress.cancel"
          @pointercancel="editPress.cancel"
          @click.capture="editPress.onClick(feed.uid, $event)"
        >
          {{ feed.name }}
        </NuxtLink>
        <IconButton
          icon="i-ph-dots-three-bold"
          :to="`/edit/${feed.uid}`"
          variant="quiet"
          size="sm"
          :aria-label="`Edit ${feed.name}`"
          class="mr-sm hidden shrink-0 [@media(hover:hover)]:group-hover:inline-flex"
        />
      </li>
    </ul>

    <HomeOptionsDrawer v-model:open="optionsOpen" />
  </div>
</template>
