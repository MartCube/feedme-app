<script setup lang="ts">
// The slowly drifting feed behind the sign-in and sign-up screens: a hint of
// what's on the other side of the form. Pure decoration — a signed-out visitor
// has no feed, so the cards are a fixed sample, not API data, and not
// FeedPostCard (which is wired to a real Post and lifts on hover).
//
// Each column renders its cards twice and moves by half its own height
// (motion.css § Drift), so the loop has no visible seam. Two columns on a
// phone, four on desktop — the extra two are hidden below lg, so the
// difference is CSS alone and SSR renders the same tree on both.
//
// Phone: in the flow, taking whatever height the form leaves above it (bled
// to the screen edges through the page inset), so however tall the copy runs
// the cards never pass behind it. Desktop: an overlay behind the whole page.
interface SamplePost {
  source: string
  date: string
  title: string
  image?: boolean
}

const posts: SamplePost[] = [
  { source: 'The Long Field', date: '21 Oct', title: 'Notes from a year of walking the same trail every morning', image: true },
  { source: 'Hacker News', date: '21 Oct', title: 'Show HN: A tiny static site generator in 300 lines' },
  { source: 'Slow Kitchen', date: '21 Oct', title: 'Why the best bread starts the night before', image: true },
  { source: 'r/typography', date: '20 Oct', title: 'The quiet return of the humanist sans' },
  { source: 'Low Tide Studio', date: '20 Oct', title: 'Building a desk out of one oak board' },
  { source: 'Orbit Weekly', date: '20 Oct', title: 'What the new lunar lander actually measures', image: true },
  { source: 'Hacker News', date: '19 Oct', title: 'Plain text is still the best file format' },
  { source: 'Field Recordings', date: '19 Oct', title: 'Forty minutes of rain on a tin roof' },
  { source: 'r/cycling', date: '19 Oct', title: 'Ten thousand kilometres on a steel frame', image: true },
  { source: 'The Margin', date: '18 Oct', title: 'On reading slowly in a fast decade' },
]

// Each column starts somewhere else in the list, so neighbours never show the
// same card side by side. Period and direction alternate (motion.css).
const columns = [
  { offset: 0, motion: 'animate-drift-up', desktopOnly: false },
  { offset: 3, motion: 'animate-drift-down', desktopOnly: false },
  { offset: 6, motion: 'animate-drift-up-slow', desktopOnly: true },
  { offset: 2, motion: 'animate-drift-down-slow', desktopOnly: true },
].map(({ offset, ...column }) => {
  const cards = [...posts.slice(offset), ...posts.slice(0, offset)]
  return { ...column, cards: [...cards, ...cards] }
})
</script>

<template>
  <!-- opacity-45: present enough to read as a feed, quiet enough that the form
       is the only thing on the screen asking to be read. -->
  <div
    aria-hidden="true"
    class="pointer-events-none -mx-lg -mt-lg mb-md flex min-h-0 flex-1 justify-between gap-sm overflow-hidden px-sm opacity-45 drift-mask lg:absolute lg:inset-0 lg:m-0 lg:gap-md lg:px-md"
  >
    <div
      v-for="(column, c) in columns"
      :key="c"
      class="h-full min-w-0 flex-1 overflow-hidden lg:max-w-64"
      :class="column.desktopOnly && 'hidden lg:block'"
    >
      <div
        class="flex flex-col gap-sm motion-reduce:animate-none"
        :class="column.motion"
      >
        <div
          v-for="(post, p) in column.cards"
          :key="p"
          class="flex flex-col gap-2xs rounded-2xl bg-elevated p-sm"
        >
          <div
            v-if="post.image"
            class="h-18 rounded-xl bg-muted lg:h-24"
          />
          <p class="text-caption text-muted">
            <span class="text-primary">{{ post.source }}</span> · {{ post.date }}
          </p>
          <p class="text-caption font-semibold lg:text-body">
            {{ post.title }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
