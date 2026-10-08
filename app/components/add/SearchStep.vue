<script setup lang="ts">
const emit = defineEmits<{ back: [], forward: [] }>()

const wizard = useAddFeedWizard()
const { type, query, loading, results, searched, error, selectedFeeds } = wizard

// Heading label/icon and placeholder all come from the type card the user
// just tapped (website when the type is somehow unset).
const typeMeta = computed(() => feedTypes.find(option => option.type === type.value) ?? feedTypes[0]!)

// Strip the protocol so the URL reads cleanly (css-tricks.com/feed/).
function displayUrl(url: string) {
  return url.replace(/^https?:\/\//, '')
}

// The fallback when a feed has no icon. UAvatar's own takes the first letter of
// the first two words, which turns "Vue.js - The progressive…" into "V-" — so
// only words that start with a letter or digit count.
function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(word => /^[\p{L}\p{N}]/u.test(word))
    .slice(0, 2)
    .map(word => word[0])
    .join('')
}
</script>

<template>
  <!-- touch-none lets vaul own the drag-to-close gesture; revisit once the
       results list needs real touch scrolling. -->
  <div class="flex h-full touch-none flex-col scroll-host bg-default page-inset">
    <header class="flex items-center justify-between gap-sm">
      <IconButton
        icon="i-ph-caret-left-bold"
        aria-label="Back"
        @click="emit('back')"
      />
      <!-- Same elevated circle as the back button; disabled only dims the icon. -->
      <button
        type="button"
        class="flex size-12 shrink-0 items-center justify-center rounded-full bg-elevated shadow-elevated transition-colors"
        :disabled="!selectedFeeds.length"
        aria-label="Continue"
        @click="emit('forward')"
      >
        <UIcon
          name="i-ph-caret-right-bold"
          class="size-6 transition-colors"
          :class="selectedFeeds.length ? 'text-default' : 'text-dimmed'"
        />
      </button>
    </header>

    <h1 class="mt-lg flex items-center gap-sm text-title tracking-tight text-inset">
      <UIcon
        :name="typeMeta.icon"
        class="size-6 text-muted"
      />
      {{ typeMeta.label }}
    </h1>

    <SearchInput
      v-model="query"
      class="mt-md"
      :placeholder="typeMeta.placeholder"
      paste
      autofocus
      @submit="wizard.search()"
    />

    <ul
      v-if="loading"
      class="mt-md flex flex-col"
    >
      <li
        v-for="n in 3"
        :key="n"
        class="flex flex-col gap-2xs py-sm"
      >
        <USkeleton class="h-4 w-2/3" />
        <USkeleton class="h-3 w-1/3" />
      </li>
    </ul>

    <!-- Tapping anywhere on a card toggles its checkbox — multi-select, the
         header's forward button advances once at least one feed is picked. -->
    <ul
      v-else-if="results.length"
      class="mt-md flex flex-col gap-sm"
    >
      <li
        v-for="result in results"
        :key="result.feed_url"
      >
        <button
          type="button"
          class="flex w-full items-center gap-sm rounded-2xl bg-elevated p-sm text-left shadow-elevated transition-colors"
          :aria-pressed="wizard.isSelected(result)"
          :aria-label="`Select ${result.name}`"
          @click="wizard.toggleFeed(result)"
        >
          <!-- Every type has a face: five channels named "One Piece" are told apart by
               their avatars, and a site by its icon. `icon` is a square proxied crop, or
               null — then, and when the image fails to load, UAvatar shows the name's
               initials. alt="" because the button's aria-label already names the feed.
               Not loading="lazy": at most five rows, all on screen, and inside the
               drawer Chrome never got round to fetching a lazy one at all. -->
          <UAvatar
            :src="result.icon ?? undefined"
            alt=""
            :text="initials(result.name)"
            size="xl"
            class="shrink-0"
            :ui="{ root: 'bg-muted', fallback: 'text-caption font-semibold text-muted uppercase' }"
          />
          <span class="min-w-0 flex-1">
            <span class="block truncate text-body">{{ result.name }}</span>
            <!-- The feed URL, not the site: one page can declare several feeds, and this
                 is the only thing that tells them apart — same reason the edit panel keeps
                 it on screen. It is also what actually gets subscribed. -->
            <!-- A source can sit in several feeds, so one you follow stays
                 pickable — the caption just says it's already in one. -->
            <span class="block truncate text-caption text-muted">
              <template v-if="result.already_subscribed">In your feeds · </template>{{ displayUrl(result.feed_url) }}
            </span>
          </span>
          <!-- Page-bg circle reads as a well punched into the card; checking
               only drops a primary checkmark in, nothing else changes. -->
          <span
            class="flex size-10 shrink-0 items-center justify-center"
            aria-hidden="true"
          >
            <span class="flex size-8 items-center justify-center rounded-full bg-default">
              <UIcon
                v-if="wizard.isSelected(result)"
                name="i-ph-check-bold"
                class="size-5 text-primary"
              />
            </span>
          </span>
        </button>
      </li>
    </ul>

    <!-- /discover resolves links, channels and subreddits, and searches YouTube by name;
         a keyword under the other cards finds nothing until T11d searches our own
         catalog. Saying so beats a blank panel. -->
    <p
      v-else-if="searched"
      class="mt-md text-body text-muted"
    >
      Nothing found. Try pasting a link.
    </p>

    <!-- The feed page's Add source commits straight from this step (it already
         knows the feed), so a refused add has to be able to say so here too. -->
    <p
      v-if="error"
      class="mt-xs text-caption text-error text-inset"
    >
      {{ error }}
    </p>
  </div>
</template>
