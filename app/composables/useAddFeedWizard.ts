import type { FeedCandidate, FeedType } from '~/assets/types'
import type { Destination } from '~/stores/feeds'

export type WizardStep = 'type' | 'input' | 'destination' | 'folder'
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
  const selectedFeeds = useState<FeedCandidate[]>('add-selected', () => [])
  const direction = useState<WizardDirection>('add-direction', () => 'forward')
  // Distinguishes "haven't searched yet" from "searched and found nothing", so
  // the step only explains itself once the user has actually asked.
  const searched = useState('add-searched', () => false)
  // The destination step commits over the network now, so it has both a busy
  // state and something to say when the server refuses.
  const adding = useState('add-adding', () => false)
  const error = useState<string | null>('add-error', () => null)

  function selectType(t: FeedType) {
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

  // Searching by keyword is T11 (GET /discover?type=&q=). The one thing that can be
  // resolved without a server is a pasted feed URL — which is where T11's website branch
  // ends up anyway — so a URL becomes a single candidate and anything else finds nothing.
  function search() {
    if (!type.value) return
    direction.value = 'forward'
    loading.value = false
    error.value = null
    // A new search invalidates prior picks — stale selections would keep the
    // forward button enabled on feeds no longer visible in the list.
    selectedFeeds.value = []
    searched.value = true
    const candidate = candidateFromUrl(query.value, type.value)
    results.value = candidate ? [candidate] : []
  }

  // Name and type here are placeholders the server overwrites: it fetches the feed and
  // takes the real title from it, and infers the type from the host. All that has to
  // survive to POST /feeds is the URL.
  function candidateFromUrl(input: string, feedType: FeedType): FeedCandidate | null {
    let url: URL
    try {
      url = new URL(input.trim())
    }
    catch {
      return null
    }
    if (url.protocol !== 'http:' && url.protocol !== 'https:') return null
    return {
      name: url.hostname.replace(/^www\./, ''),
      feed_url: url.href,
      site_url: url.origin,
      type: feedType,
      icon_url: '',
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
      error.value = detailOf(failure)
      return false
    }
    finally {
      adding.value = false
    }
  }

  // The API's one error shape, {"detail": string}, as ofetch hands it back.
  function detailOf(failure: unknown) {
    const detail = (failure as { data?: { detail?: string } })?.data?.detail
    return detail || 'Couldn\'t add that feed.'
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
