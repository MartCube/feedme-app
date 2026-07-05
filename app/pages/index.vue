<script setup lang="ts">
useHead({ title: 'FeedMe' })

// Shared with the /settings/:panel? route (same component, see nuxt.config):
// a stable key keeps this page mounted across those navigations.
definePageMeta({ key: 'home' })

const feedsStore = useFeedsStore()
const { folders, looseFeeds } = storeToRefs(feedsStore)
const { memberFeeds, isExpanded, toggleFolder } = feedsStore

const addItems = [
  [
    { label: 'New feed', icon: 'i-ph-rss-bold', to: '/add' },
    // TODO: point at the folder-create drawer once it exists (see docs/screens-and-flows.md §7).
    { label: 'New folder', icon: 'i-ph-folder-bold', onSelect: () => {} },
  ],
]
</script>

<template>
  <main class="flex flex-col px-8 pt-8 pb-12">
    <Navbar>
      <IconButton
        icon="i-ph-list-bold"
        to="/settings"
        aria-label="Menu"
      />
      <UDropdownMenu :items="addItems">
        <IconButton
          icon="i-ph-plus-bold"
          aria-label="Add"
        />
      </UDropdownMenu>
    </Navbar>

    <h1 class="mt-8 text-2xl font-semibold tracking-tight">
      Feeds
    </h1>

    <ul
      v-auto-animate
      class="mt-2 flex flex-col"
    >
      <template
        v-for="folder in folders"
        :key="folder.uid"
      >
        <li class="flex items-center border-b border-silver-200">
          <NuxtLink
            :to="`/feed/${folder.uid}`"
            class="flex min-w-0 flex-1 items-baseline gap-2 py-4"
          >
            <span class="truncate text-xl leading-8">{{ folder.name }}</span>
            <span class="text-sm text-muted">{{ folder.feed_uids.length }}</span>
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
            class="border-b border-silver-200"
          >
            <NuxtLink
              :to="`/feed/${feed.uid}`"
              :class="['block truncate py-4 pl-6 text-xl leading-8', folder.muted_feed_uids.includes(feed.uid) && 'text-muted opacity-60']"
            >
              {{ feed.name }}
            </NuxtLink>
          </li>
        </template>
      </template>

      <li
        v-for="feed in looseFeeds"
        :key="feed.uid"
        class="border-b border-silver-200"
      >
        <NuxtLink
          :to="`/feed/${feed.uid}`"
          class="block truncate py-4 text-xl leading-8"
        >
          {{ feed.name }}
        </NuxtLink>
      </li>
    </ul>
  </main>
</template>
