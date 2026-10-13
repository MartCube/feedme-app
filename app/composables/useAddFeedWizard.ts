import type { FeedCandidate, FeedType } from '~/assets/types'

export type WizardStep = 'type' | 'input' | 'destination' | 'new-feed'
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
  // The feed page's "Add source": the feed is already chosen, so the search
  // step commits straight into it and the destination step never shows. Set
  // by the opener before it navigates to /add; reset() clears it with the rest.
  const target = useState<string | null>('add-target', () => null)

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
    selectedFeeds.value = isSelected(feed)
      ? selectedFeeds.value.filter(f => f.feed_url !== feed.feed_url)
      : [...selectedFeeds.value, feed]
  }

  function proceedToDestination() {
    if (!selectedFeeds.value.length) return
    direction.value = 'forward'
    step.value = 'destination'
  }

  // Every add awaits and answers with the feed it landed in, or null: the host
  // only closes on success — and then opens that feed — because a URL that
  // isn't a feed comes back as a 422 the step has to show. The candidates go
  // in one at a time — a refusal stops the rest, and the ones already in stay in.
  async function run(work: () => Promise<string>, fallback: string): Promise<string | null> {
    if (!selectedFeeds.value.length || adding.value) return null
    adding.value = true
    error.value = null
    try {
      return await work()
    }
    catch (failure) {
      error.value = detailOf(failure, fallback)
      return null
    }
    finally {
      adding.value = false
    }
  }

  // Into one of the user's feeds — the destination step's pick, or the target.
  function addTo(feedUid: string) {
    return run(async () => {
      for (const candidate of selectedFeeds.value) await feedsStore.addSource(feedUid, candidate)
      return feedUid
    }, 'Couldn\'t add that source.')
  }

  // A new feed holding the picks: created with the first, so a first URL that
  // isn't a feed leaves no empty feed behind, then the rest join it. A blank
  // name takes the first source's own title (the backend's default).
  function addToNewFeed(name: string) {
    return run(async () => {
      const [first, ...rest] = selectedFeeds.value
      const feed = await feedsStore.addFeed({ name, candidate: first })
      for (const candidate of rest) await feedsStore.addSource(feed.uid, candidate)
      return feed.uid
    }, 'Couldn\'t create that feed.')
  }

  // The API's one error shape, {"detail": string}, as ofetch hands it back. A network
  // failure carries no body at all, which is what the fallback is for.
  function detailOf(failure: unknown, fallback: string) {
    const detail = (failure as { data?: { detail?: string } })?.data?.detail
    return detail || fallback
  }

  function goToNewFeed() {
    direction.value = 'forward'
    error.value = null
    step.value = 'new-feed'
  }

  function back() {
    direction.value = 'back'
    // A failure belongs to the attempt that caused it — stepping back and forward again
    // is a fresh one, and the old line under it would be a lie.
    error.value = null
    if (step.value === 'new-feed') step.value = 'destination'
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
    target.value = null
  }

  return { step, type, query, loading, results, searched, adding, error, selectedFeeds, direction, target, selectType, search, isSelected, toggleFeed, proceedToDestination, addTo, addToNewFeed, goToNewFeed, back, reset }
}
