# Add-feed flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the UI/UX for adding a feed as a three-phase in-drawer wizard (pick type → search/paste → choose destination), backed by a mock search.

**Architecture:** The existing `app/components/add/Drawer.vue` bottom sheet becomes the wizard host. Phase is component state shared through a `useAddFeedWizard()` composable; the three phases are separate step components swapped with a slide transition. A mock `mockSearch()` returns fixed per-type results after ~1s. Committing writes through a new `useFeedsStore().addFeed()` action, then the drawer closes and the home list reflects it.

**Tech Stack:** Nuxt 4 (SSR on), Vue 3 `<script setup>`, Pinia (setup stores), Nuxt UI 4 (`UDrawer`, `UInput`, `UButton`, `USkeleton`, `UIcon`), Tailwind v4, `@iconify-json/ph` icons.

## Global Constraints

- **House style (verbatim):** 2-space indent, single quotes, no semicolons. **No `<style>` blocks in components** — non-utility CSS goes in the global CSS layer (`app/assets/css/main.css` and its imports: `transitions.css`, `themes.css`, `typography.css`). Slide/transition CSS belongs in `transitions.css`.
- **No test harness.** Verify each task with `pnpm lint` (expect no errors) + driving the flow in the running app (`pnpm dev`, open `/add`). The user manually reviews and tests between tasks. Do **not** add a test framework.
- **Visual taste:** no divider lines in lists, no glossy rings; rely on spacing + soft shadows (`bg-elevated` + `shadow-elevated`). Use theme tokens (`text-body`, `text-caption`, `text-muted`, `text-title`, `bg-default`, `bg-elevated`), not raw color ramps.
- **Component naming:** files under `app/components/add/` register folder-prefixed (`add/TypeStep.vue` → `<AddTypeStep>`). Files under `app/components/ui/` register unprefixed (`<IconButton>`).
- **Scope:** one feed → one destination. No multi-select, no Reddit connect UI, no real search/RSS. See `docs/superpowers/specs/2026-07-07-add-feed-flow-design.md`.

---

### Task 1: Search result type + mock search

**Files:**
- Modify: `app/assets/types.ts` (append the `FeedCandidate` type)
- Create: `app/assets/mock-search.ts`

**Interfaces:**
- Consumes: `Feed`, `FeedType` from `app/assets/types.ts`.
- Produces:
  - `type FeedCandidate = Omit<Feed, 'uid'>` — a search result (a feed we haven't subscribed to yet).
  - `mockSearch(type: FeedType, query: string): Promise<FeedCandidate[]>` — resolves a fixed per-type list after ~1s, ignoring `query`.

- [ ] **Step 1: Add the `FeedCandidate` type**

Append to `app/assets/types.ts`:

```ts
// A search result before it is subscribed: a candidate feed with no uid yet.
// Becomes a Feed (uid generated) when the user adds it.
export type FeedCandidate = Omit<Feed, 'uid'>
```

- [ ] **Step 2: Create the mock search**

Create `app/assets/mock-search.ts`:

```ts
import type { FeedCandidate, FeedType } from './types'

// No backend yet: the query is ignored and each type returns the same fixed
// short list, after a ~1s delay so it feels like results arriving.
const RESULTS: Record<FeedType, FeedCandidate[]> = {
  website: [
    { name: 'CSS-Tricks', feed_url: 'https://css-tricks.com/feed/', site_url: 'https://css-tricks.com', type: 'website' },
    { name: 'Smashing Magazine', feed_url: 'https://www.smashingmagazine.com/feed/', site_url: 'https://www.smashingmagazine.com', type: 'website' },
    { name: 'A List Apart', feed_url: 'https://alistapart.com/main/feed/', site_url: 'https://alistapart.com', type: 'website' },
  ],
  youtube: [
    { name: 'Fireship', feed_url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCsBjURrPoezykLs9EqgamOA', site_url: 'https://www.youtube.com/@Fireship', type: 'youtube' },
    { name: 'Vue Mastery', feed_url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCG5UOTNKA1Fv5vBaMxg98rw', site_url: 'https://www.youtube.com/@VueMastery', type: 'youtube' },
    { name: 'Theo - t3.gg', feed_url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCbRP3c757lWg9M-U7TyEkXA', site_url: 'https://www.youtube.com/@t3dotgg', type: 'youtube' },
  ],
  reddit: [
    { name: 'r/vuejs', feed_url: 'https://www.reddit.com/r/vuejs/.rss', site_url: 'https://www.reddit.com/r/vuejs', type: 'reddit' },
    { name: 'r/webdev', feed_url: 'https://www.reddit.com/r/webdev/.rss', site_url: 'https://www.reddit.com/r/webdev', type: 'reddit' },
    { name: 'r/programming', feed_url: 'https://www.reddit.com/r/programming/.rss', site_url: 'https://www.reddit.com/r/programming', type: 'reddit' },
  ],
}

export function mockSearch(type: FeedType, _query: string): Promise<FeedCandidate[]> {
  return new Promise(resolve => setTimeout(() => resolve(RESULTS[type]), 1000))
}
```

- [ ] **Step 3: Lint**

Run: `pnpm lint`
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add app/assets/types.ts app/assets/mock-search.ts
git commit -m "feat(add): add FeedCandidate type and mock search"
```

---

### Task 2: Store `addFeed` action

**Files:**
- Modify: `app/stores/feeds.ts`

**Interfaces:**
- Consumes: `FeedCandidate` (Task 1), existing `feeds` / `folders` refs and `Feed`, `Folder` types.
- Produces:
  - `type Destination = 'loose' | string` — `'loose'` (top level) or a folder uid.
  - `addFeed(candidate: FeedCandidate, destination: Destination): Feed` on `useFeedsStore()` — pushes a new `Feed` (generated `feed_*` uid) into `feeds`; if `destination` is a folder uid, appends the uid to that folder's `feed_uids`. Returns the created feed.

- [ ] **Step 1: Add the `Destination` type and `addFeed` action**

In `app/stores/feeds.ts`, update the type import and add the action inside the store setup, then export it.

Change the import line to include `FeedCandidate`:

```ts
import type { Feed, FeedCandidate, Folder, Post } from '~/assets/types'
```

Add this type above the `export const useFeedsStore` line:

```ts
// Where a newly added feed lands: the top-level list, or a folder by uid.
export type Destination = 'loose' | string
```

Inside the store setup (after `memberFeeds`), add:

```ts
function addFeed(candidate: FeedCandidate, destination: Destination): Feed {
  const feed: Feed = { ...candidate, uid: `feed_${crypto.randomUUID()}` }
  feeds.value = [...feeds.value, feed]

  if (destination !== 'loose') {
    const folder = folders.value.find(f => f.uid === destination)
    if (folder) {
      folder.feed_uids = [...folder.feed_uids, feed.uid]
    }
  }

  return feed
}
```

- [ ] **Step 2: Export the action**

Add `addFeed` to the store's returned object:

```ts
return { feeds, folders, posts, looseFeeds, memberFeeds, expandedFolderUids, isExpanded, toggleFolder, addFeed }
```

- [ ] **Step 3: Lint**

Run: `pnpm lint`
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add app/stores/feeds.ts
git commit -m "feat(add): add feeds store addFeed action"
```

---

### Task 3: `useAddFeedWizard` composable

**Files:**
- Create: `app/composables/useAddFeedWizard.ts`

**Interfaces:**
- Consumes: `FeedCandidate`, `FeedType` (Task 1); `useFeedsStore`, `Destination` (Task 2); `mockSearch` (Task 1); Nuxt `useState` (auto-imported).
- Produces `useAddFeedWizard()` returning:
  - state refs: `step: Ref<WizardStep>`, `type: Ref<FeedType | null>`, `query: Ref<string>`, `loading: Ref<boolean>`, `results: Ref<FeedCandidate[]>`, `selectedFeed: Ref<FeedCandidate | null>`, `direction: Ref<WizardDirection>`.
  - actions: `selectType(t: FeedType)`, `search()`, `pickFeed(feed: FeedCandidate)`, `chooseDestination(dest: Destination)`, `back()`, `reset()`.
  - exported types: `type WizardStep = 'type' | 'input' | 'destination'`, `type WizardDirection = 'forward' | 'back'`.

- [ ] **Step 1: Create the composable**

Create `app/composables/useAddFeedWizard.ts`:

```ts
import type { FeedCandidate, FeedType } from '~/assets/types'
import type { Destination } from '~/stores/feeds'
import { mockSearch } from '~/assets/mock-search'

export type WizardStep = 'type' | 'input' | 'destination'
export type WizardDirection = 'forward' | 'back'

// Shared, SSR-safe wizard state (useState) so every step component and the
// Drawer host read/drive the same flow. reset() is called by the Drawer once
// the sheet has fully closed.
export function useAddFeedWizard() {
  const feedsStore = useFeedsStore()

  const step = useState<WizardStep>('add-step', () => 'type')
  const type = useState<FeedType | null>('add-type', () => null)
  const query = useState('add-query', () => '')
  const loading = useState('add-loading', () => false)
  const results = useState<FeedCandidate[]>('add-results', () => [])
  const selectedFeed = useState<FeedCandidate | null>('add-selected', () => null)
  const direction = useState<WizardDirection>('add-direction', () => 'forward')

  function selectType(t: FeedType) {
    type.value = t
    direction.value = 'forward'
    step.value = 'input'
  }

  async function search() {
    if (!type.value) return
    direction.value = 'forward'
    loading.value = true
    results.value = []
    results.value = await mockSearch(type.value, query.value)
    loading.value = false
  }

  function pickFeed(feed: FeedCandidate) {
    selectedFeed.value = feed
    direction.value = 'forward'
    step.value = 'destination'
  }

  function chooseDestination(dest: Destination) {
    if (!selectedFeed.value) return
    feedsStore.addFeed(selectedFeed.value, dest)
  }

  function back() {
    direction.value = 'back'
    if (step.value === 'destination') step.value = 'input'
    else if (step.value === 'input') step.value = 'type'
  }

  function reset() {
    step.value = 'type'
    type.value = null
    query.value = ''
    loading.value = false
    results.value = []
    selectedFeed.value = null
    direction.value = 'forward'
  }

  return { step, type, query, loading, results, selectedFeed, direction, selectType, search, pickFeed, chooseDestination, back, reset }
}
```

- [ ] **Step 2: Lint**

Run: `pnpm lint`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add app/composables/useAddFeedWizard.ts
git commit -m "feat(add): add useAddFeedWizard composable"
```

Note: Tasks 1–3 are pure logic with no UI yet; they are exercised end-to-end in Task 7. Their gate here is lint only.

---

### Task 4: Type-picker step (phase 1)

**Files:**
- Create: `app/components/add/TypeStep.vue`

**Interfaces:**
- Consumes: `FeedType` from `~/assets/types`.
- Produces: `<AddTypeStep>` — emits `select: [type: FeedType]`. Renders the "Add feed" title and the three type rows.

- [ ] **Step 1: Create the component**

Create `app/components/add/TypeStep.vue`:

```vue
<script setup lang="ts">
import type { FeedType } from '~/assets/types'

const emit = defineEmits<{ select: [type: FeedType] }>()

const types: { type: FeedType, label: string, hint: string, icon: string }[] = [
  { type: 'website', label: 'Website', hint: 'Any site or RSS feed', icon: 'i-ph-globe-bold' },
  { type: 'youtube', label: 'YouTube', hint: 'Channels by link or search', icon: 'i-ph-youtube-logo-bold' },
  { type: 'reddit', label: 'Reddit', hint: 'Subreddits by link or search', icon: 'i-ph-reddit-logo-bold' },
]
</script>

<template>
  <div>
    <h1 class="text-title tracking-tight">
      Add feed
    </h1>

    <ul class="mt-8 flex flex-col gap-2">
      <li
        v-for="option in types"
        :key="option.type"
      >
        <button
          type="button"
          class="flex w-full items-center gap-4 rounded-2xl bg-elevated px-4 py-4 text-left shadow-elevated transition-colors"
          @click="emit('select', option.type)"
        >
          <UIcon
            :name="option.icon"
            class="size-6 shrink-0 text-muted"
          />
          <span class="min-w-0 flex-1">
            <span class="block text-body">{{ option.label }}</span>
            <span class="block text-caption text-muted">{{ option.hint }}</span>
          </span>
          <UIcon
            name="i-ph-caret-right-bold"
            class="size-5 shrink-0 text-muted"
          />
        </button>
      </li>
    </ul>
  </div>
</template>
```

- [ ] **Step 2: Lint**

Run: `pnpm lint`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add app/components/add/TypeStep.vue
git commit -m "feat(add): add type-picker step"
```

---

### Task 5: Search step (phase 2)

**Files:**
- Create: `app/components/add/SearchStep.vue`

**Interfaces:**
- Consumes: `useAddFeedWizard` (Task 3) for `type`, `query`, `loading`, `results`, `search`; `IconButton`; `FeedCandidate`.
- Produces: `<AddSearchStep>` — emits `back: []` and `pick: [feed: FeedCandidate]`. Renders back + type header, the input with a Paste chip / submit, a loading skeleton, and the results list.

- [ ] **Step 1: Create the component**

Create `app/components/add/SearchStep.vue`:

```vue
<script setup lang="ts">
import type { FeedCandidate } from '~/assets/types'

const emit = defineEmits<{ back: [], pick: [feed: FeedCandidate] }>()

const wizard = useAddFeedWizard()
const { type, query, loading, results } = wizard

const typeLabel = computed(() => {
  switch (type.value) {
    case 'youtube': return 'YouTube'
    case 'reddit': return 'Reddit'
    default: return 'Website'
  }
})

// Browsers block silent clipboard reads, so the Paste chip reads on tap (a user
// gesture). It shows only while the input is empty.
async function paste() {
  try {
    const text = await navigator.clipboard.readText()
    if (text) query.value = text
  }
  catch {
    // clipboard blocked/empty — the user can type instead
  }
}

// Strip the protocol so the result's site reads cleanly (css-tricks.com).
function displayUrl(url: string) {
  return url.replace(/^https?:\/\//, '')
}
</script>

<template>
  <div class="flex flex-col">
    <div class="flex items-center gap-2">
      <IconButton
        icon="i-ph-arrow-left-bold"
        size="sm"
        aria-label="Back"
        @click="emit('back')"
      />
      <h2 class="text-body font-semibold">
        {{ typeLabel }}
      </h2>
    </div>

    <form
      class="mt-6"
      @submit.prevent="wizard.search()"
    >
      <UInput
        v-model="query"
        placeholder="Paste a link or search…"
        size="xl"
        class="w-full"
      >
        <template #trailing>
          <UButton
            v-if="!query"
            label="Paste"
            color="neutral"
            variant="soft"
            size="sm"
            @click="paste"
          />
          <UButton
            v-else
            icon="i-ph-arrow-right-bold"
            color="neutral"
            variant="ghost"
            size="sm"
            type="submit"
            aria-label="Search"
          />
        </template>
      </UInput>
    </form>

    <ul
      v-if="loading"
      class="mt-6 flex flex-col gap-5"
    >
      <li
        v-for="n in 3"
        :key="n"
        class="flex flex-col gap-2"
      >
        <USkeleton class="h-4 w-2/3" />
        <USkeleton class="h-3 w-1/3" />
      </li>
    </ul>

    <ul
      v-else-if="results.length"
      class="mt-4 flex flex-col"
    >
      <li
        v-for="result in results"
        :key="result.feed_url"
        class="flex items-center gap-3 py-3"
      >
        <div class="min-w-0 flex-1">
          <p class="truncate text-body">
            {{ result.name }}
          </p>
          <p class="truncate text-caption text-muted">
            {{ displayUrl(result.site_url) }}
          </p>
        </div>
        <IconButton
          icon="i-ph-plus-bold"
          size="sm"
          aria-label="Add feed"
          @click="emit('pick', result)"
        />
      </li>
    </ul>
  </div>
</template>
```

- [ ] **Step 2: Lint**

Run: `pnpm lint`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add app/components/add/SearchStep.vue
git commit -m "feat(add): add search step with paste chip and results"
```

---

### Task 6: Destination step (phase 3)

**Files:**
- Create: `app/components/add/DestinationStep.vue`

**Interfaces:**
- Consumes: `useFeedsStore` `folders`; `Destination` (Task 2); `IconButton`.
- Produces: `<AddDestinationStep>` — emits `back: []` and `choose: [destination: Destination]`. Renders "Add to" header, a top-level row, then a row per folder.

- [ ] **Step 1: Create the component**

Create `app/components/add/DestinationStep.vue`:

```vue
<script setup lang="ts">
import type { Destination } from '~/stores/feeds'

const emit = defineEmits<{ back: [], choose: [destination: Destination] }>()

const feedsStore = useFeedsStore()
const { folders } = storeToRefs(feedsStore)
</script>

<template>
  <div class="flex flex-col">
    <div class="flex items-center gap-2">
      <IconButton
        icon="i-ph-arrow-left-bold"
        size="sm"
        aria-label="Back"
        @click="emit('back')"
      />
      <h2 class="text-body font-semibold">
        Add to
      </h2>
    </div>

    <ul class="mt-6 flex flex-col">
      <li>
        <button
          type="button"
          class="flex w-full items-baseline gap-2 py-4 text-left"
          @click="emit('choose', 'loose')"
        >
          <span class="min-w-0 flex-1 truncate text-body">Feeds</span>
          <span class="text-caption text-muted">Top level</span>
        </button>
      </li>
      <li
        v-for="folder in folders"
        :key="folder.uid"
      >
        <button
          type="button"
          class="flex w-full items-baseline gap-2 py-4 text-left"
          @click="emit('choose', folder.uid)"
        >
          <span class="min-w-0 flex-1 truncate text-body">{{ folder.name }}</span>
          <span class="text-caption text-muted">{{ folder.feed_uids.length }}</span>
        </button>
      </li>
    </ul>
  </div>
</template>
```

- [ ] **Step 2: Lint**

Run: `pnpm lint`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add app/components/add/DestinationStep.vue
git commit -m "feat(add): add destination-picker step"
```

---

### Task 7: Wire the Drawer host + slide transitions

**Files:**
- Modify: `app/components/add/Drawer.vue` (replace the mock body with the wizard host)
- Modify: `app/assets/css/transitions.css` (append the `wizard-*` transition classes, matching the existing `page-slide`/`panel-slide` house pattern)

**Interfaces:**
- Consumes: `useAddFeedWizard` (Task 3); `Destination` (Task 2); `<AddTypeStep>` (Task 4), `<AddSearchStep>` (Task 5), `<AddDestinationStep>` (Task 6); `IconButton`.
- Produces: the fully wired `/add` wizard. Closing (✕, drag, or browser back) routes home; on full close the wizard resets. Choosing a destination commits via the composable then closes.

- [ ] **Step 1: Append the slide-transition classes to `transitions.css`**

Add to the end of `app/assets/css/transitions.css`, matching the house curve/duration used by `page-slide-*` and `panel-slide-*` (`0.35s cubic-bezier(0.32, 0.72, 0, 1)`):

```css
/* Add-feed wizard step transitions (see components/add/Drawer.vue).
   forward = advancing a phase (slide in from the right); back = the back
   button (slide in from the left). Used with a <Transition mode="out-in">,
   so steps do not overlap — a subtle offset + fade reads as a push without
   a blank gap. Curve/duration match page-slide/panel-slide above. */
.wizard-forward-enter-active,
.wizard-forward-leave-active,
.wizard-back-enter-active,
.wizard-back-leave-active {
  transition: transform 0.35s cubic-bezier(0.32, 0.72, 0, 1), opacity 0.35s cubic-bezier(0.32, 0.72, 0, 1);
}

.wizard-forward-enter-from {
  transform: translateX(24px);
  opacity: 0;
}

.wizard-forward-leave-to {
  transform: translateX(-24px);
  opacity: 0;
}

.wizard-back-enter-from {
  transform: translateX(-24px);
  opacity: 0;
}

.wizard-back-leave-to {
  transform: translateX(24px);
  opacity: 0;
}
```

- [ ] **Step 2: Replace `Drawer.vue` with the wizard host**

Overwrite `app/components/add/Drawer.vue`:

```vue
<script setup lang="ts">
// Hosts the add-feed wizard bottom sheet. Like the settings drawer, the /add
// URL renders the home page component (see the pages:extend hook in
// nuxt.config) so the feed list stays mounted behind the sheet. This component
// opens the drawer on /add, drives the three-phase wizard (type → input →
// destination) via useAddFeedWizard, routes home on close, and resets the
// wizard once the sheet has fully closed.
import type { Destination } from '~/stores/feeds'

const route = useRoute()
const open = ref(false)

const onAdd = computed(() => route.path === '/add')

// vaul emits animationEnd(false) for its initial closed state — only a close
// that follows a completed open animation should navigate home.
const hasOpened = ref(false)

const wizard = useAddFeedWizard()
const { step, direction } = wizard

watch(onAdd, (on) => {
  open.value = on
})

onMounted(() => {
  if (onAdd.value) {
    open.value = true
  }
})

function close() {
  open.value = false
}

function onAnimationEnd(isOpen: boolean) {
  if (isOpen) {
    hasOpened.value = true
  }
  else if (hasOpened.value && onAdd.value) {
    navigateTo('/')
  }
  // Once the sheet is fully closed, clear wizard state so it reopens fresh.
  if (!isOpen) {
    wizard.reset()
  }
}

function onChoose(destination: Destination) {
  wizard.chooseDestination(destination)
  close()
}
</script>

<template>
  <UDrawer
    v-model:open="open"
    :handle="false"
    :ui="{
      // overflow-hidden clips the panel to the sheet's rounded top corners.
      content: 'mt-0 h-full max-h-full overflow-hidden',
      container: 'grow gap-0 p-0 overflow-hidden',
      body: 'relative overflow-hidden',
    }"
    @animation-end="onAnimationEnd"
  >
    <template #body>
      <!-- touch-none lets vaul own the drag-to-close gesture; revisit once the
           results list needs real touch scrolling. -->
      <div class="h-full touch-none overflow-y-auto bg-default px-8 pt-6 pb-12">
        <div class="flex justify-end">
          <IconButton
            icon="i-ph-x-bold"
            aria-label="Close add feed"
            @click="close"
          />
        </div>

        <Transition
          :name="direction === 'forward' ? 'wizard-forward' : 'wizard-back'"
          mode="out-in"
        >
          <AddTypeStep
            v-if="step === 'type'"
            key="type"
            class="mt-4"
            @select="wizard.selectType"
          />
          <AddSearchStep
            v-else-if="step === 'input'"
            key="input"
            class="mt-4"
            @back="wizard.back"
            @pick="wizard.pickFeed"
          />
          <AddDestinationStep
            v-else
            key="destination"
            class="mt-4"
            @back="wizard.back"
            @choose="onChoose"
          />
        </Transition>
      </div>
    </template>
  </UDrawer>
</template>
```

- [ ] **Step 3: Lint**

Run: `pnpm lint`
Expected: no errors.

- [ ] **Step 4: Verify the full flow in the app**

Run: `pnpm dev`, open the app, tap the navbar **+** (or navigate to `/add`). Confirm end-to-end:
- Phase 1 shows Website / YouTube / Reddit; tapping one slides right to phase 2.
- Phase 2 shows the type as the header with a back button; an empty input shows a **Paste** chip; typing shows the submit arrow; submitting shows a ~1s skeleton then 3 results (title + site, no leading type icon).
- Tapping a result's **+** slides to phase 3 ("Add to") with **Feeds (Top level)** + the **Dev** folder.
- Tapping **Feeds** adds the feed loose and closes; it appears in the home list. Reopen, add another into **Dev**; it appears under the Dev folder (expand it).
- Back buttons step back one phase; ✕ and drag-down close the sheet; reopening starts at phase 1 (state reset).

- [ ] **Step 5: Commit**

```bash
git add app/components/add/Drawer.vue app/assets/css/transitions.css
git commit -m "feat(add): wire add-feed wizard host and slide transitions"
```

---

### Task 8: Update docs

**Files:**
- Modify: `docs/screens-and-flows.md` (screen 4)
- Modify: `docs/current-state.md`

**Interfaces:** none (documentation only).

- [ ] **Step 1: Rewrite screen 4 in `docs/screens-and-flows.md`**

Replace the body of section "## 4. Add feed" (keep the heading) so it describes the shipped wizard instead of the "visual demonstration only" mock. Cover: the three phases (pick type → paste/search → choose destination), slide-right transitions + back button, the mock search returning fixed per-type results, one-feed-to-one-destination scope, and that Reddit's connect step is deferred (`pending_tasks/reddit-connect.md`). Point at the components: `add/Drawer.vue` (host), `add/TypeStep.vue`, `add/SearchStep.vue`, `add/DestinationStep.vue`, and `useAddFeedWizard()`.

- [ ] **Step 2: Update `docs/current-state.md`**

Read the file first, then update the relevant status line(s) so the add-feed flow is listed as built (wizard + mock search + `addFeed` store action) rather than a mock/placeholder, matching the surrounding format.

- [ ] **Step 3: Lint**

Run: `pnpm lint`
Expected: no errors (markdown is not linted, but confirm the command still passes clean).

- [ ] **Step 4: Commit**

```bash
git add docs/screens-and-flows.md docs/current-state.md
git commit -m "docs: describe the shipped add-feed wizard"
```

---

## Notes for the implementer

- **Nuxt UI slot names** (`#trailing` on `UInput`) and component props (`USkeleton` sizing via utility classes) follow Nuxt UI 4. If a prop/slot differs in the installed version, check `node_modules/@nuxt/ui` rather than guessing.
- **`crypto.randomUUID()`** is available in the browser and Node 18+; no import needed.
- **Auto-imports:** `ref`, `computed`, `watch`, `onMounted`, `useRoute`, `navigateTo`, `useState`, `storeToRefs`, `useFeedsStore`, and `useAddFeedWizard` are all auto-imported — do not add manual imports for them. Only `import type` for types and the explicit `mockSearch` import are needed.
