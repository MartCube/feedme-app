<script setup lang="ts">
const emit = defineEmits<{ back: [], close: [], forward: [] }>()

const wizard = useAddFeedWizard()
const { type, query, loading, results, searched, error, selectedFeeds } = wizard

// Heading label/icon and placeholder all come from the type card the user
// just tapped (website when the type is somehow unset).
const typeMeta = computed(() => feedTypes.find(option => option.type === type.value) ?? feedTypes[0]!)

// Continue lights primary once, the moment the first pick makes it available,
// so the eye goes from the card just checked to the way forward. Held as long
// as the tap flash (useTapSelection); the colour fades in and out on the
// standard transition.
const canContinue = computed(() => selectedFeeds.value.length > 0)
const continueBlink = ref(false)
let blinkTimer: ReturnType<typeof setTimeout> | undefined
watch(canContinue, (can) => {
  if (!can) return
  continueBlink.value = true
  clearTimeout(blinkTimer)
  blinkTimer = setTimeout(() => {
    continueBlink.value = false
  }, 450)
})
onScopeDispose(() => clearTimeout(blinkTimer))

// Strip the protocol so the URL reads cleanly (css-tricks.com/feed/).
function displayUrl(url: string) {
  return url.replace(/^https?:\/\//, '')
}

// "412K subscribers" — compact, the way YouTube itself shows it.
const compact = new Intl.NumberFormat(undefined, { notation: 'compact', maximumFractionDigits: 1 })
function subscriberLabel(count: number) {
  return `${compact.format(count)} ${count === 1 ? 'subscriber' : 'subscribers'}`
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
  <div class="flex h-full touch-none flex-col scroll-host bg-default page-inset *:max-w-reading">
    <header class="flex items-center justify-between gap-sm">
      <!-- Close then Back hold the leading side on every step, as a bound
           pair like the post's actions; Continue stands alone on the far side. -->
      <div class="flex shrink-0 items-center gap-xs">
        <IconButton
          icon="i-ph-x-bold"
          aria-label="Close add feed"
          @click="emit('close')"
        />
        <IconButton
          icon="i-ph-caret-left-bold"
          aria-label="Back"
          @click="emit('back')"
        />
      </div>
      <!-- Same elevated circle and tooltip as an IconButton (not one itself:
           disabled only dims the icon, and enabled it rests text-default, a
           step louder than an IconButton's muted icon). -->
      <UTooltip
        text="Continue"
        :content="{ side: 'top', sideOffset: 4, collisionPadding: 2 }"
      >
        <button
          type="button"
          class="flex size-12 shrink-0 items-center justify-center rounded-full bg-elevated shadow-elevated transition-colors"
          :disabled="!canContinue"
          aria-label="Continue"
          @click="emit('forward')"
        >
          <UIcon
            name="i-ph-caret-right-bold"
            class="size-6 transition-colors"
            :class="continueBlink ? 'text-primary' : canContinue ? 'text-default' : 'text-dimmed'"
          />
        </button>
      </UTooltip>
    </header>

    <h1 class="mt-lg flex items-center gap-sm text-title tracking-tight">
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
         header's forward button advances once at least one feed is picked. The
         card isn't the button itself: its link out would be interactive inside
         interactive. The select button stretches over the whole card instead
         (absolute inset-0), and the link sits above it (relative z-10) — the
         post card's pattern; isolate keeps that z-10 inside the card. -->
    <ul
      v-else-if="results.length"
      class="mt-md flex flex-col gap-sm"
    >
      <li
        v-for="result in results"
        :key="result.feed_url"
        class="relative isolate flex items-center gap-sm rounded-2xl bg-elevated p-sm shadow-elevated transition-colors hover-lift"
      >
        <button
          type="button"
          class="absolute inset-0 rounded-2xl"
          :aria-pressed="wizard.isSelected(result)"
          :aria-label="`Select ${result.name}`"
          @click="wizard.toggleFeed(result)"
        />
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
          <!-- A YouTube search hit says how big the channel is; anything else shows its
               feed URL, not the site: one page can declare several feeds, and this is the
               only thing that tells them apart. A source can sit in several feeds, so one
               you follow stays pickable — the caption just says it's already in one,
               after the short count but before a URL that truncates anyway. -->
          <span class="block truncate text-caption text-muted">
            <template v-if="result.subscribers !== null">
              {{ subscriberLabel(result.subscribers) }}<template v-if="result.already_subscribed"> · In your feeds</template>
            </template>
            <template v-else>
              <template v-if="result.already_subscribed">In your feeds · </template>{{ displayUrl(result.feed_url) }}
            </template>
          </span>
        </span>
        <!-- The channel or site itself, in a new tab — to judge it before
             picking it. -->
        <a
          v-if="result.site_url"
          :href="result.site_url"
          target="_blank"
          rel="noopener noreferrer"
          :aria-label="`Open ${result.name} in a new tab`"
          class="group/icon relative z-10 flex size-10 shrink-0 items-center justify-center rounded-full"
        >
          <UIcon
            name="i-ph-arrow-square-out-bold"
            class="size-5 text-muted transition-colors [@media(hover:hover)]:group-hover/icon:text-primary"
          />
        </a>
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
