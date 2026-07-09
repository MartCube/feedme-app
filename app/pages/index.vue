<script setup lang="ts">
useHead({ title: 'FeedMe' })

// Shared with the /settings/:panel? route (same component, see nuxt.config):
// a stable key keeps this page mounted across those navigations.
definePageMeta({ key: 'home' })

const feedsStore = useFeedsStore()
const { folders, looseFeeds } = storeToRefs(feedsStore)
const { memberFeeds, isExpanded, toggleFolder } = feedsStore

const { selectedUid, select } = useTapSelection()
</script>

<template>
  <main class="flex flex-col px-md pt-lg pb-xl">
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

    <h1 class="mt-lg text-title tracking-tight">
      Feeds
    </h1>

    <ul
      v-auto-animate
      class="mt-md flex flex-col"
    >
      <template
        v-for="folder in folders"
        :key="folder.uid"
      >
        <li class="flex items-center">
          <NuxtLink
            :to="`/feed/${folder.uid}`"
            class="-ml-sm flex min-w-0 flex-1 items-baseline gap-xs rounded-2xl py-sm pl-sm pr-sm transition-colors"
            :class="selectedUid === folder.uid && 'bg-elevated shadow-elevated'"
            @pointerdown="select(folder.uid)"
          >
            <span class="truncate text-body">{{ folder.name }}</span>
            <span class="text-caption text-muted">{{ folder.feed_uids.length }}</span>
          </NuxtLink>
          <UButton
            icon="i-ph-caret-down-bold"
            variant="ghost"
            color="neutral"
            size="md"
            :aria-expanded="isExpanded(folder.uid)"
            :aria-label="isExpanded(folder.uid) ? `Collapse ${folder.name}` : `Expand ${folder.name}`"
            :ui="{ base: 'rounded-full' }"
            :class="['transition-transform duration-200', isExpanded(folder.uid) && 'rotate-180']"
            @click="toggleFolder(folder.uid)"
          />
        </li>
        <template v-if="isExpanded(folder.uid)">
          <li
            v-for="feed in memberFeeds(folder)"
            :key="`${folder.uid}_${feed.uid}`"
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
      >
        <NuxtLink
          :to="`/feed/${feed.uid}`"
          class="-mx-sm block truncate rounded-2xl px-sm py-sm text-body transition-colors"
          :class="selectedUid === feed.uid && 'bg-elevated shadow-elevated'"
          @pointerdown="select(feed.uid)"
        >
          {{ feed.name }}
        </NuxtLink>
      </li>
    </ul>
  </main>
</template>
