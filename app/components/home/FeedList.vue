<script setup lang="ts">
// The home feed list: wordmark → Home row → pinned Saved group → folders →
// loose feeds. Rendered by the mobile home page and, on desktop, by the sidebar
// — so all list state (tap flash, long-press edit, options sheet) lives here,
// not in the page. `activeUid` is the desktop master–detail selection: the open
// feed's row keeps the elevated treatment persistently.
// No top margin of its own — the gap above the wordmark is page context (the
// mobile page clears its navbar; the desktop sidebar starts flush).
const props = defineProps<{ activeUid?: string | null }>()

const feedsStore = useFeedsStore()
const { folders, looseFeeds, savedCounts } = storeToRefs(feedsStore)
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

// A row's trailing 3-dot: revealed by hover — or keyboard focus, or it would be
// unreachable without a pointer — on hover-capable pointers only. The two
// flavours differ on touch: folders and loose feeds hide it there, where
// long-press is the entry, while Home has no long-press and keeps its own.
// (hover:hover) and (hover:none) never both match, so the two rules can't race.
const ROW_ACTION = 'hidden [@media(hover:hover)]:group-hover:inline-flex [@media(hover:hover)]:group-focus-within:inline-flex'
const ROW_ACTION_TOUCH = `${ROW_ACTION} [@media(hover:none)]:inline-flex`

// Long-press a folder or loose-feed row to edit it (mobile); the same edit
// route is reached on desktop via the hover-revealed 3-dot on the row.
const editPress = useLongPress(uid => navigateTo(`/edit/${uid}`))

const optionsOpen = ref(false)

// Tap feedback for the plain icon triggers (the chevrons), same primary flash
// as IconButton — which the 3-dots get from IconButton itself.
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
    <!-- Stand-in wordmark until a designer supplies a real one: FEED in the
         theme's accent, ME in body ink. text-logo is a brand-only size that
         sits outside the four-size scale on purpose (typography.css). -->
    <h1 class="text-logo tracking-tight">
      <span class="text-primary">FEED</span>ME
    </h1>

    <!-- Home is a list row like the rest — same height, same surface, same
         hover-revealed 3-dot. Its only differences: "All feeds" sits inline
         where a folder keeps its count, and the 3-dot opens the options sheet
         instead of linking to /edit. -->
    <div
      class="group -mx-sm mt-md flex items-center rounded-2xl transition-colors"
      :class="isCards || isActive('all') ? 'bg-elevated shadow-elevated' : 'hover-highlight'"
    >
      <NuxtLink
        to="/feed/all"
        class="flex min-w-0 flex-1 items-baseline gap-xs py-sm pl-sm"
        @pointerdown="select('all')"
      >
        <span class="truncate text-body">Home</span>
        <span class="text-caption text-muted">All feeds</span>
      </NuxtLink>
      <IconButton
        icon="i-ph-dots-three-bold"
        variant="quiet"
        size="sm"
        aria-label="Feed options"
        class="mr-sm shrink-0"
        :class="ROW_ACTION_TOUCH"
        @click="optionsOpen = true"
      />
    </div>

    <!-- Cards-mode spacing is per-row margins, not a ul gap: md between
         top-level cards, xs for the plain member rows inside a dropdown. In
         list mode the rows run contiguously, Home included. -->
    <ul
      v-auto-animate
      class="flex flex-col"
      :class="isCards && 'mt-md'"
    >
      <!-- Pinned Saved group: same split row as folders (link + chevron), but
           its members are the fixed saved groups, not store feeds. Expansion
           reuses expandedFolderUids under the literal 'saved' uid. -->
      <li
        class="-mx-sm flex items-center rounded-2xl transition-colors"
        :class="isCards ? 'bg-elevated shadow-elevated mt-md first:mt-0' : isActive('saved') ? 'bg-elevated shadow-elevated' : 'hover-highlight'"
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
            class="-mr-sm flex items-baseline gap-xs rounded-2xl py-sm pl-md pr-sm text-body transition-colors"
            :class="isActive(group.uid) ? 'bg-elevated shadow-elevated' : 'hover-highlight'"
            @pointerdown="select(group.uid)"
          >
            <span class="truncate">{{ group.name }}</span>
            <!-- Same muted count a folder row carries, for the same reason:
                 how much is in there without opening it. -->
            <span class="text-caption text-muted">{{ savedCounts[group.group] }}</span>
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
          :class="isCards ? 'bg-elevated shadow-elevated mt-md first:mt-0' : isActive(folder.uid) ? 'bg-elevated shadow-elevated' : 'hover-highlight'"
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
          <IconButton
            icon="i-ph-dots-three-bold"
            :to="`/edit/${folder.uid}`"
            variant="quiet"
            size="sm"
            :aria-label="`Edit ${folder.name}`"
            class="shrink-0"
            :class="ROW_ACTION"
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
                isActive(feed.uid) ? 'bg-elevated shadow-elevated' : 'hover-highlight',
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
        :class="isCards ? 'bg-elevated shadow-elevated mt-md first:mt-0' : isActive(feed.uid) ? 'bg-elevated shadow-elevated' : 'hover-highlight'"
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
          class="mr-sm shrink-0"
          :class="ROW_ACTION"
        />
      </li>
    </ul>

    <HomeOptionsDrawer v-model:open="optionsOpen" />
  </div>
</template>
