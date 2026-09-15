import type { FeedCandidate, FeedType } from '~/assets/types'
import type { Destination } from '~/stores/feeds'

export type WizardStep = 'type' | 'input' | 'destination' | 'folder'
export type WizardDirection = 'forward' | 'back'

// Shared, SSR-safe wizard state (useState) so every step component and the
// Drawer host read/drive the same flow. reset() is called by the Drawer once
// the sheet has fully closed.
export function useAddFeedWizard() {
  const feedsStore = useFeedsStore()
  const { $api } = useNuxtApp()

  const step = useState<WizardStep>('add-step', () => 'type')
  const type = useState<FeedType | null>('add-type', () => null)
  const query = useState('add-query', () => '')
  const loading = useState('add-loading', () => false)
  const results = useState<FeedCandidate[]>('add-results', () => [])
  const selectedFeeds = useState<FeedCandidate[]>('add-selected', () => [])
  const direction = useState<WizardDirection>('add-direction', () => 'forward')
  // Distinguishes "haven't searched yet" from "searched and found nothing", so
  // the step only explains itself once the user has actually asked.
  const searched = useState('add-searched', () => false)
  // The destination step commits over the network now, so it has both a busy
  // state and something to say when the server refuses.
  const adding = useState('add-adding', () => false)
  const error = useState<string | null>('add-error', () => null)
  // Which search the results on screen belong to. Shared like everything else here,
  // not a local: a second submit while the first is in flight would otherwise let the
  // slower answer land last and win, and the Drawer's reset() has to be able to
  // disown an in-flight search from a step component that is already gone.
  const searchSeq = useState('add-search-seq', () => 0)

  function selectType(t: FeedType) {
    searchSeq.value++
    // Re-picking a type (e.g. back to phase 1, then a different type) must clear
    // the previous type's search — otherwise stale, wrong-typed results would
    // show, and could even be added under the wrong type.
    query.value = ''
    results.value = []
    loading.value = false
    searched.value = false
    error.value = null
    selectedFeeds.value = []
    type.value = t
    direction.value = 'forward'
    step.value = 'input'
  }

  // GET /discover resolves the query: a pasted page becomes the feeds it declares, a
  // channel URL or a subreddit name becomes its feed, and a name under the YouTube card
  // is a channel search. A keyword under the other cards still finds nothing — searching
  // our own catalog for one is T11d. An empty list is a normal answer, so only a request
  // that actually failed sets `error` — including the 503 YouTube answers when its API
  // won't, which is not "nothing found" and shouldn't read like it.
  async function search() {
    if (!type.value) return
    const attempt = ++searchSeq.value
    direction.value = 'forward'
    loading.value = true
    error.value = null
    // A new search invalidates prior picks — stale selections would keep the
    // forward button enabled on feeds no longer visible in the list.
    selectedFeeds.value = []
    searched.value = true
    try {
      const found = await $api<FeedCandidate[]>('/discover', {
        query: { type: type.value, q: query.value.trim() },
      })
      if (attempt !== searchSeq.value) return
      results.value = found
    }
    catch (failure) {
      if (attempt !== searchSeq.value) return
      results.value = []
      error.value = detailOf(failure, 'Couldn\'t search right now.')
    }
    finally {
      if (attempt === searchSeq.value) loading.value = false
    }
  }

  function isSelected(feed: FeedCandidate) {
    return selectedFeeds.value.some(f => f.feed_url === feed.feed_url)
  }

  function toggleFeed(feed: FeedCandidate) {
    // Nothing to pick: POST /feeds answers 422 on a duplicate, so the row says
    // "Following" instead of buying that error one step later.
    if (feed.already_subscribed) return
    selectedFeeds.value = isSelected(feed)
      ? selectedFeeds.value.filter(f => f.feed_url !== feed.feed_url)
      : [...selectedFeeds.value, feed]
  }

  function proceedToDestination() {
    if (!selectedFeeds.value.length) return
    direction.value = 'forward'
    step.value = 'destination'
  }

  // Awaited, and reports whether it worked: the host only closes the sheet on success,
  // because a URL that isn't a feed comes back as a 422 this step has to show.
  async function chooseDestination(dest: Destination): Promise<boolean> {
    if (!selectedFeeds.value.length || adding.value) return false
    adding.value = true
    error.value = null
    try {
      for (const feed of selectedFeeds.value) await feedsStore.addFeed(feed, dest)
      return true
    }
    catch (failure) {
      error.value = detailOf(failure, 'Couldn\'t add that feed.')
      return false
    }
    finally {
      adding.value = false
    }
  }

  // The API's one error shape, {"detail": string}, as ofetch hands it back. A network
  // failure carries no body at all, which is what the fallback is for.
  function detailOf(failure: unknown, fallback: string) {
    const detail = (failure as { data?: { detail?: string } })?.data?.detail
    return detail || fallback
  }

  function goToNewFolder() {
    direction.value = 'forward'
    step.value = 'folder'
  }

  async function createFolder(name: string) {
    if (!name.trim()) return
    await feedsStore.addFolder(name)
    // Returning is a pop: the destination list slides back in (from the left)
    // with the new folder in place.
    direction.value = 'back'
    step.value = 'destination'
  }

  function back() {
    direction.value = 'back'
    // A failure belongs to the attempt that caused it — stepping back and forward again
    // is a fresh one, and the old line under it would be a lie.
    error.value = null
    if (step.value === 'folder') step.value = 'destination'
    else if (step.value === 'destination') step.value = 'input'
    else if (step.value === 'input') step.value = 'type'
  }

  function reset() {
    // any search still in flight belongs to the flow being thrown away
    searchSeq.value++
    step.value = 'type'
    type.value = null
    query.value = ''
    loading.value = false
    results.value = []
    searched.value = false
    adding.value = false
    error.value = null
    selectedFeeds.value = []
    direction.value = 'forward'
  }

  return { step, type, query, loading, results, searched, adding, error, selectedFeeds, direction, selectType, search, isSelected, toggleFeed, proceedToDestination, chooseDestination, goToNewFolder, createFolder, back, reset }
}
