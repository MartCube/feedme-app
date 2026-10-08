<script setup lang="ts">
// The home feed list: wordmark → Home row → pinned Saved row → feeds. Flat on
// purpose: a feed is already the group (one source or many), and everything
// you'd do to one — its sources, their on/off, a rename — lives on its feed
// page, reached by tapping its title. Rendered by the mobile home page and, on
// desktop, by the sidebar — so the tap flash lives here, not in the page.
// `activeUid` is the desktop master–detail selection: the open feed's row
// keeps the elevated treatment persistently.
// No top margin of its own — the gap above the wordmark is page context (the
// mobile page clears its navbar; the desktop sidebar starts flush).
const props = defineProps<{ activeUid?: string | null }>()

const { feeds, savedCounts } = storeToRefs(useFeedsStore())

const settings = useSettingsStore()
// Cards mode: every row keeps the elevated surface permanently — the tap
// flash merges into it, and the name's accent is the cue.
const isCards = computed(() => settings.feedListStyle === 'cards')

const { selectedUid, select } = useTapSelection()

// Mobile tap flash OR persistent desktop selection. The Saved row also stays
// lit while one of its groups is open.
function isActive(uid: string) {
  return selectedUid.value === uid || props.activeUid === uid
    || (uid === 'saved' && Boolean(props.activeUid?.startsWith('saved_')))
}

// The row treatment every row shares. Selected lights the row's *name*
// primary — the tap flash on the way out, the master–detail selection standing
// still — and adds the elevated surface; everything else takes the desktop
// hover accent (themes.css). Selection rides the name rather than the surface
// because in cards mode every row already has a surface, so the name is the
// only cue left there.
function rowClass(uid: string) {
  return [
    isCards.value || isActive(uid) ? 'bg-elevated shadow-elevated' : '',
    isActive(uid) ? 'text-primary' : 'hover-accent',
  ]
}

const savedTotal = computed(() => savedCounts.value.bookmarks + savedCounts.value.favorites + savedCounts.value.later)
</script>

<template>
  <div class="flex flex-col">
    <!-- Stand-in wordmark until a designer supplies a real one: FEED in the
         theme's accent, ME in body ink. text-logo is a brand-only size that
         sits outside the four-size scale on purpose (typography.css). The
         link is inside the h1 and sized to the text, so only the wordmark is
         a target — a block link would make the whole row's dead space
         clickable. It goes where the Home row goes.
         Desktop pins it: the h-12 row is the top-row axis the posts pane's
         title and the post pane's actions share, and the sidebar's inset is
         pulled into its own padding (box-content, so h-12 stays the row) so
         rows scroll away under an opaque sunken strip rather than past it. -->
    <h1 class="text-logo tracking-tight lg:sticky lg:-top-lg lg:z-10 lg:-mx-lg lg:-mt-lg lg:box-content lg:flex lg:h-12 lg:items-center lg:bg-sunken lg:px-lg lg:pt-lg">
      <NuxtLink to="/feed/all">
        <span class="text-primary">FEED</span>ME
      </NuxtLink>
    </h1>

    <!-- Cards-mode spacing is per-row margins, md between cards. List mode runs
         the rows on the smallest step, so a selected row's rounded surface
         doesn't fuse with the row above it. -->
    <ul
      v-auto-animate
      class="mt-md flex flex-col"
      :class="!isCards && 'gap-2xs'"
    >
      <!-- items-center, not items-baseline like the counted rows: "All feeds"
           is a word, and on a shared baseline a 12px word beside a 16px one
           reads as sagging — centring the two line boxes lifts it the ~1px
           that fixes it, without a magic offset. -->
      <li
        class="-mx-sm rounded-2xl transition-colors"
        :class="rowClass('all')"
      >
        <NuxtLink
          to="/feed/all"
          class="flex min-w-0 items-center gap-xs p-sm"
          @pointerdown="select('all')"
        >
          <span class="truncate text-body">Home</span>
          <span class="text-caption text-muted">All feeds</span>
        </NuxtLink>
      </li>

      <!-- Pinned Saved row. Its three groups are on its feed page, the same
           place a feed lists its sources. -->
      <li
        class="-mx-sm rounded-2xl transition-colors"
        :class="[rowClass('saved'), isCards && 'mt-md']"
      >
        <NuxtLink
          to="/feed/saved"
          class="flex min-w-0 items-baseline gap-xs p-sm"
          @pointerdown="select('saved')"
        >
          <span class="truncate text-body">Saved</span>
          <span
            v-if="savedTotal"
            class="text-caption text-muted"
          >{{ savedTotal }}</span>
        </NuxtLink>
      </li>

      <li
        v-for="feed in feeds"
        :key="feed.uid"
        class="-mx-sm rounded-2xl transition-colors"
        :class="[rowClass(feed.uid), isCards && 'mt-md']"
      >
        <!-- A group carries its source count, the way the Saved row carries
             its total; a one-source feed is just its name. -->
        <NuxtLink
          :to="`/feed/${feed.uid}`"
          class="flex min-w-0 items-baseline gap-xs p-sm"
          @pointerdown="select(feed.uid)"
        >
          <span class="truncate text-body">{{ feed.name }}</span>
          <span
            v-if="feed.sources.length !== 1"
            class="text-caption text-muted"
          >{{ feed.sources.length }}</span>
        </NuxtLink>
      </li>
    </ul>
  </div>
</template>
