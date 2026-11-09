<script setup lang="ts">
import type { FeedCandidate } from '~/assets/types'

// One search result. Tapping the card picks it — one source per pass, straight
// on to Destination. Above that layer, two things of its own: the caption's link
// to the channel or site (judge it outside the app), and Preview (judge it here).
const props = defineProps<{ result: FeedCandidate }>()
const emit = defineEmits<{ pick: [] }>()

const isDesktop = useIsDesktop()
const wizard = useAddFeedWizard()
const { previews, previewing } = wizard

// A channel or subreddit carries its platform's mark; a website's link is
// marked as leaving the app — the post card's meta row (FeedPostMeta) says it
// the same way.
const linkIcon = computed(() => props.result.type === 'website'
  ? 'i-ph-arrow-square-out-bold'
  : feedTypes.find(option => option.type === props.result.type)?.icon)

// What the caption's link says. A website shows its feed URL, not the site: one
// page can declare several feeds, and this is the only thing that tells them
// apart. A subreddit is recognised by its r/name, which its title often isn't.
const linkText = computed(() => {
  const { type, feed_url, site_url } = props.result
  if (type === 'youtube') return 'YouTube'
  if (type === 'reddit') {
    const name = site_url?.match(/\/r\/([^/?#]+)/)?.[1]
    if (name) return `r/${name}`
  }
  return displayUrl(feed_url)
})

// What follows the link: how big a YouTube search hit is, and whether this
// source already sits in one of your feeds (it stays pickable — a source can
// sit in several).
const captionRest = computed(() => [
  props.result.subscribers !== null ? subscriberLabel(props.result.subscribers) : null,
  props.result.already_subscribed ? 'In your feeds' : null,
].filter(Boolean).map(part => ` · ${part}`).join(''))

// Strip the protocol so the URL reads cleanly (css-tricks.com/feed/).
function displayUrl(url: string) {
  return url.replace(/^https?:\/\//, '')
}

// "412K subs" — compact like YouTube's own count, and short enough that the
// caption stays on one line on a phone.
const compact = new Intl.NumberFormat(undefined, { notation: 'compact', maximumFractionDigits: 1 })
function subscriberLabel(count: number) {
  return `${compact.format(count)} ${count === 1 ? 'sub' : 'subs'}`
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

// The Preview button says how the fetch went, on itself: nothing else on screen
// changes until posts arrive. Previewing is desktop's — there the preview sits
// beside the list and this button closes it; on a phone the preview is a step
// of its own, and coming back from it leaves the button at Preview.
const state = computed(() => previews.value[props.result.feed_url])
const isPreviewing = computed(() => isDesktop.value && previewing.value?.feed_url === props.result.feed_url)

// No tooltip: hover text is for the icon-only action buttons in a title row,
// and this chip's label already says its state. The aria label keeps the name:
// a screen reader lands on the button without the row around it.
const button = computed(() => {
  const name = props.result.name
  if (isPreviewing.value) return { label: 'Previewing', aria: `Close preview of ${name}`, tone: 'text-primary' }
  switch (state.value?.status) {
    case 'loading':
      return { label: 'Preview', aria: `Loading preview of ${name}`, tone: 'text-muted' }
    case 'error':
      return { label: 'Couldn\'t load', aria: `${state.value.detail} Try again`, tone: 'text-error' }
    case 'empty':
      return { label: 'No posts yet', aria: `${name} has no posts yet`, tone: 'text-muted' }
    default:
      return { label: 'Preview', aria: `Preview ${name}`, tone: 'text-default' }
  }
})

function onPreview() {
  if (isPreviewing.value) wizard.closePreview()
  else if (state.value?.status !== 'loading') wizard.preview(props.result)
}
</script>

<template>
  <!-- The card isn't the button itself: its link out and Preview would be
       interactive inside interactive. The pick button stretches over the whole
       card instead (absolute inset-0), and the link and Preview sit above it
       (relative z-10) — the post card's pattern; isolate keeps that z-10
       inside the card. -->
  <li class="group relative isolate flex items-center gap-sm rounded-2xl bg-elevated p-sm shadow-elevated transition-colors hover-lift">
    <button
      type="button"
      class="absolute inset-0 rounded-2xl"
      :aria-label="`Add ${result.name}`"
      @click="emit('pick')"
    />
    <!-- Every type has a face: five channels named "One Piece" are told apart by
         their avatars, and a site by its icon. `icon` is a square proxied crop, or
         null — then, and when the image fails to load, UAvatar shows the name's
         initials. alt="" because the button's aria-label already names the feed.
         Not loading="lazy": at most five rows, all on screen, and inside the
         drawer Chrome never got round to fetching a lazy one at all. Its
         surface flips with the card's hover like the Preview chip's: a site icon
         is often transparent, and on a hovered (bg-muted) card a bg-muted disc
         would leave the logo floating with no edge. -->
    <UAvatar
      :src="result.icon ?? undefined"
      alt=""
      :text="initials(result.name)"
      size="xl"
      class="shrink-0"
      :ui="{ root: 'bg-muted transition-colors group-hover:bg-elevated', fallback: 'text-caption font-semibold text-muted uppercase' }"
    />
    <span class="flex min-w-0 flex-1 flex-col gap-2xs">
      <!-- Wraps to two lines rather than truncating: "Veritasium en español" and
           four near-namesakes are only told apart by the end of the name. Never
           tinted while previewing: the chip's Previewing marks the open one. -->
      <span class="line-clamp-2 text-body">{{ result.name }}</span>
      <span class="text-caption text-muted">
        <a
          v-if="result.site_url"
          :href="result.site_url"
          target="_blank"
          rel="noopener noreferrer"
          class="relative z-10 inline-flex max-w-full items-center gap-2xs align-bottom text-primary transition-colors hover-darken"
        >
          <UIcon
            :name="linkIcon!"
            class="size-4 shrink-0"
          />
          <span class="truncate underline underline-offset-2">{{ linkText }}</span>
        </a>
        <template v-else>{{ linkText }}</template>{{ captionRest }}
      </span>
    </span>
    <!-- The Paste chip, always one surface step off the card under it. At rest
         the card is bg-elevated, so the chip takes bg-muted (neutral soft's own
         bg-elevated would be no surface at all). A hovered card turns bg-muted —
         the input's surface — so the chip flips to bg-elevated, exactly the
         Paste chip on its input. The hover:, active: and disabled: classes
         restate the same pair over neutral soft's own, each of which would
         otherwise sink the chip into the card. Its label alone carries the
         state; the chip's width follows the label, which is fine — it's
         right-aligned and the name column flexes. -->
    <UButton
      :label="button.label"
      color="neutral"
      variant="soft"
      size="sm"
      class="relative z-10 shrink-0 bg-muted group-hover:bg-elevated hover:bg-elevated active:bg-elevated disabled:bg-muted group-hover:disabled:bg-elevated"
      :class="state?.status === 'loading' && 'animate-pulse'"
      :ui="{ label: `transition-colors ${button.tone}` }"
      :disabled="state?.status === 'empty'"
      :aria-label="button.aria"
      :aria-busy="state?.status === 'loading' || undefined"
      @click="onPreview"
    />
  </li>
</template>
