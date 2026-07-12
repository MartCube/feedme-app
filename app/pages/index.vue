<script setup lang="ts">
useHead({ title: 'FeedMe' })

// Shared with the /settings/:panel? route (same component, see nuxt.config):
// a stable key keeps this page mounted across those navigations.
definePageMeta({ key: 'home' })

const feedsStore = useFeedsStore()
const { folders, looseFeeds } = storeToRefs(feedsStore)
const { memberFeeds, isExpanded, toggleFolder } = feedsStore

const settings = useSettingsStore()
// Cards mode: only top-level rows (Saved, folders, loose feeds) keep the
// elevated surface permanently — their tap flash merges into it (the icon
// accent flash stays the cue). Member rows stay plain and keep the flash.
const isCards = computed(() => settings.feedListStyle === 'cards')

const { selectedUid, select } = useTapSelection()

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
  <main class="flex flex-col page-inset">
    <Navbar>
      <IconButton
        icon="i-ph-list-bold"
        to="/settings"
        aria-label="Menu"
      />
      <IconButton
        icon="i-ph-plus-bold"
        to="/add"
        aria-label="Add"
      />
    </Navbar>

    <!-- Home is a list row like the rest (same surface, flash, cards
         treatment), linking to the merged all-feeds read. Its extras: the
         "All feeds" caption and the 3-dot options trigger sitting where the
         folder rows keep their chevron. -->
    <div
      class="-mx-sm mt-lg flex items-center rounded-2xl transition-colors"
      :class="(isCards || selectedUid === 'all') && 'bg-elevated shadow-elevated'"
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
        :class="isCards ? 'bg-elevated shadow-elevated mt-md first:mt-0' : selectedUid === 'saved' && 'bg-elevated shadow-elevated'"
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
            :class="selectedUid === group.uid && 'bg-elevated shadow-elevated'"
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
          class="-mx-sm flex items-center rounded-2xl transition-colors"
          :class="isCards ? 'bg-elevated shadow-elevated mt-md first:mt-0' : selectedUid === folder.uid && 'bg-elevated shadow-elevated'"
        >
          <NuxtLink
            :to="`/feed/${folder.uid}`"
            class="flex min-w-0 flex-1 items-baseline gap-xs py-sm pl-sm"
            @pointerdown="select(folder.uid)"
          >
            <span class="truncate text-body">{{ folder.name }}</span>
            <span class="text-caption text-muted">{{ folder.feed_uids.length }}</span>
          </NuxtLink>
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
                selectedUid === feed.uid && 'bg-elevated shadow-elevated',
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
        :class="isCards && 'mt-md first:mt-0'"
      >
        <NuxtLink
          :to="`/feed/${feed.uid}`"
          class="-mx-sm block truncate rounded-2xl px-sm py-sm text-body transition-colors"
          :class="(isCards || selectedUid === feed.uid) && 'bg-elevated shadow-elevated'"
          @pointerdown="select(feed.uid)"
        >
          {{ feed.name }}
        </NuxtLink>
      </li>
    </ul>

    <HomeOptionsDrawer v-model:open="optionsOpen" />
  </main>
</template>
