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
// `grouped` is the desktop sidebar's shape: a slot after Saved for its own
// entries, and the feeds folded under a Feeds header. `icons` puts an icon on
// the pinned rows (Appearance → Sidebar icons); the feeds never carry one.
const props = defineProps<{ activeUid?: string | null, grouped?: boolean, icons?: boolean }>()

const { feeds } = storeToRefs(useFeedsStore())

const settings = useSettingsStore()
// The rows' fold slide (fold-rows, motion.css) waits for the first toggle:
// the group mounts open on page load, and the rows would slide in.
const feedsFolded = ref(false)

const { selectedUid, select } = useTapSelection()

// Mobile tap flash OR persistent desktop selection.
function isActive(uid: string) {
  return selectedUid.value === uid || props.activeUid === uid
}

// The row treatment every row shares. Selected lights the row's name primary
// and adds the elevated surface — the tap flash on the way out, the
// master–detail selection standing still; everything else takes the desktop
// hover accent (themes.css). A slotted row that isn't a feed (the sidebar's
// New feed) passes its own `active`.
function rowClass(uid: string, active = isActive(uid)) {
  return active ? 'bg-elevated shadow-elevated text-primary' : 'hover-accent'
}

// The icons rest muted, a step quieter than their labels, so they follow the
// row's hover accent by the same gate instead of inheriting it (as in
// settings/Home.vue).
function iconClass(uid: string) {
  return isActive(uid) ? 'text-primary' : 'text-muted [@media(hover:hover)]:group-hover:text-primary'
}

// Spins beside the wordmark while any API call is in flight. Debounced so a
// call that answers inside 150ms never flashes it.
const { $apiPending } = useNuxtApp()
const busy = refDebounced(computed(() => $apiPending.value > 0), 150)
</script>

<template>
  <div class="flex flex-col">
    <!-- The mark (ui/Logo.vue) and the wordmark: Feed in the theme's accent,
         Me in body ink, like the mark's two stacks. text-logo is a brand-only size that
         sits outside the four-size scale on purpose (typography.css). The
         link is inside the h1 and sized to the text, so only the wordmark is
         a target — a block link would make the whole row's dead space
         clickable. It goes where the Home row goes.
         Desktop pins it: the h-10 row is the top-row axis every pane's first
         row shares (page-inset, spacing.css), and the sidebar's inset is
         pulled into its own padding (box-content, so h-10 stays the row) so
         rows scroll away under an opaque sunken strip rather than past it.
         shrink-0: an overflowing sidebar column would otherwise squeeze the
         row to its text, and every fold that ends the overflow would jump. -->
    <h1 class="flex items-center gap-sm text-logo tracking-tight lg:sticky lg:-top-md lg:z-10 lg:-mx-lg lg:-mt-md lg:box-content lg:h-10 lg:shrink-0 lg:bg-sunken lg:px-lg lg:pt-md">
      <NuxtLink
        to="/feed/all"
        class="flex items-center gap-xs"
      >
        <Logo class="size-8" />
        <span><span class="text-primary">Feed</span>Me</span>
      </NuxtLink>
      <!-- Stock spinner as a stand-in until the app has its own
           (pending_tasks/custom-spinner.md). -->
      <UIcon
        v-if="busy"
        name="i-ph-circle-notch-bold"
        aria-hidden="true"
        class="size-5 animate-spin text-muted"
      />
    </h1>

    <!-- The rows run on the smallest step, so a selected row's rounded
         surface doesn't fuse with the row above it. -->
    <ul class="mt-md flex flex-col gap-2xs">
      <!-- items-center, not items-baseline like the counted feed rows: these
           carry no count, and an icon centres on its label. -->
      <li
        class="-mx-sm rounded-2xl transition-colors"
        :class="rowClass('all')"
      >
        <NuxtLink
          to="/feed/all"
          class="group flex min-w-0 items-center gap-sm p-sm lg:py-xs"
          @pointerdown="select('all')"
        >
          <UIcon
            v-if="icons"
            name="i-ph-house-bold"
            class="size-5 shrink-0 transition-colors"
            :class="iconClass('all')"
          />
          <span class="truncate text-body">Home</span>
        </NuxtLink>
      </li>

      <li
        class="-mx-sm rounded-2xl transition-colors"
        :class="rowClass('saved')"
      >
        <NuxtLink
          to="/feed/saved"
          class="group flex min-w-0 items-center gap-sm p-sm lg:py-xs"
          @pointerdown="select('saved')"
        >
          <UIcon
            v-if="icons"
            name="i-ph-bookmark-simple-bold"
            class="size-5 shrink-0 transition-colors"
            :class="iconClass('saved')"
          />
          <span class="truncate text-body">Saved</span>
        </NuxtLink>
      </li>

      <slot
        name="pinned"
        :row-class="rowClass"
      />
    </ul>

    <!-- Ungrouped it's always open and has no header. The collapsible
         animates the fold in CSS; auto-animate only the rows coming and going.
         The content box takes the rows' -mx-sm bleed back as padding: it
         clips while it folds, and would shave the row surfaces' edges.
         Grouped, the rows also fade with the fold: a height fold alone only
         wipes static rows off at the clip edge, and when nothing below the
         group moves with it (the sidebar's last group) that wipe reads as
         stutter. It's Nuxt UI's own fold animation with its own fade-in/out
         keyframes added on the same 200ms — keyframes, not a transition,
         because Reka zeroes transitions while it measures the rows. The rows
         also slide with the fold (fold-rows, motion.css), so they move
         instead of being wiped; pt-xs, not mt-xs, since the slide moves by
         the box's height and a margin would collapse out of it. -->
    <UCollapsible
      :open="!grouped || settings.feedsGroupOpen"
      class="flex flex-col"
      :class="grouped ? 'mt-lg' : 'mt-2xs'"
      :ui="{ content: grouped ? '-mx-sm px-sm data-[state=open]:animate-[collapsible-down_200ms_var(--ease-out),fade-in_200ms_var(--ease-out)] data-[state=closed]:animate-[collapsible-up_200ms_var(--ease-out),fade-out_200ms_var(--ease-out)]' : '-mx-sm px-sm' }"
      @update:open="settings.feedsGroupOpen = $event; feedsFolded = true"
    >
      <template
        v-if="grouped"
        #default="{ open }"
      >
        <GroupToggle
          label="Feeds"
          :open="open"
        />
      </template>
      <template #content>
        <ul
          v-auto-animate
          class="flex flex-col gap-2xs"
          :class="[grouped && 'pt-xs', feedsFolded && 'fold-rows']"
        >
          <li
            v-for="feed in feeds"
            :key="feed.uid"
            class="-mx-sm rounded-2xl transition-colors"
            :class="rowClass(feed.uid)"
          >
            <!-- A group carries its source count; a one-source feed is just
               its name. -->
            <NuxtLink
              :to="`/feed/${feed.uid}`"
              class="flex min-w-0 items-baseline gap-xs p-sm lg:py-xs"
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
      </template>
    </UCollapsible>
  </div>
</template>
