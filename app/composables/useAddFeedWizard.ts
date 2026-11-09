import type { DiscoverPost, Feed, FeedCandidate, FeedType, Source } from '~/assets/types'

// 'preview' is the phone's: there the preview is a step inside the drawer. On
// desktop it opens in the posts pane beside the wizard instead (DesktopShell),
// and the step never changes.
export type WizardStep = 'type' | 'input' | 'preview' | 'destination' | 'new-feed'
export type WizardDirection = 'forward' | 'back'

// A result's Preview button, per feed_url. No entry is Idle. 'ready' doubles as
// the cache, so Back → Preview again opens without a second fetch.
export type PreviewState
  = | { status: 'loading' }
    | { status: 'error', detail: string }
    | { status: 'empty' }
    | { status: 'ready', posts: DiscoverPost[] }

// The one preview fetch in flight, so starting another can cancel it. A plain
// module variable, not useState: an AbortController doesn't serialise, and a
// preview only ever starts from a click, so this never exists on the server.
let previewFetch: { feedUrl: string, controller: AbortController } | null = null

// Shared, SSR-safe wizard state (useState) so every step component, the
// Drawer host and the desktop shell read/drive the same flow. reset() is
// called by the hosts once the wizard has closed — closing throws the whole
// flow away, search and previews included.
export function useAddFeedWizard() {
  const feedsStore = useFeedsStore()
  const { $api } = useNuxtApp()

  const step = useState<WizardStep>('add-step', () => 'type')
  const type = useState<FeedType | null>('add-type', () => null)
  const query = useState('add-query', () => '')
  const loading = useState('add-loading', () => false)
  const results = useState<FeedCandidate[]>('add-results', () => [])
  // One source per pass: tapping a result picks it and moves on. Several sources
  // into one feed is several passes (the feed page's Add source makes that cheap).
  const picked = useState<FeedCandidate | null>('add-picked', () => null)
  const previews = useState<Record<string, PreviewState>>('add-previews', () => ({}))
  // The candidate whose posts are open: the phone's preview step, or the
  // desktop posts pane.
  const previewing = useState<FeedCandidate | null>('add-previewing', () => null)
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
  // The feed page's "Add source": the feed is already chosen, so picking a
  // result commits straight into it and the destination step never shows. Set
  // by the opener before it navigates to /add; reset() clears it with the rest.
  const target = useState<string | null>('add-target', () => null)
  // A source page's "New feed from this source": the feed the source may leave once
  // the new one exists. Set by startOwnFeed(); reset() clears it.
  const origin = useState<{ feedUid: string, sourceUid: string, feedName: string } | null>('add-origin', () => null)

  // Previews belong to the result list they were started from: a new search, a
  // new type or a closed wizard drops them, and the fetch still in flight.
  function clearPreviews() {
    const inFlight = previewFetch
    previewFetch = null
    inFlight?.controller.abort()
    previews.value = {}
    previewing.value = null
  }

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
    picked.value = null
    clearPreviews()
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
    clearPreviews()
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

  // Cancelling sends that result's button back to Idle: it was never answered.
  function cancelPreviewFetch() {
    const inFlight = previewFetch
    if (!inFlight) return
    previewFetch = null
    inFlight.controller.abort()
    const { [inFlight.feedUrl]: _, ...rest } = previews.value
    previews.value = rest
  }

  // GET /discover/posts, live and never stored. Only posts open anything: loading,
  // a failure and an empty feed all show on the result's button. One fetch at a
  // time — starting another cancels this one. Measured answers take 0.2–1.3s and a
  // slow site several seconds, so 10s without one is a failure, not a wait.
  async function preview(candidate: FeedCandidate) {
    const feedUrl = candidate.feed_url
    const known = previews.value[feedUrl]
    if (known?.status === 'ready') return openPreview(candidate)
    if (known?.status === 'loading') return
    cancelPreviewFetch()
    const controller = new AbortController()
    previewFetch = { feedUrl, controller }
    previews.value = { ...previews.value, [feedUrl]: { status: 'loading' } }
    // The timeout aborts the same controller by hand: ofetch ignores its own
    // `timeout` whenever a `signal` is passed. A cancel or a reset unsets
    // previewFetch before aborting, so a fetch that is no longer the current one
    // was disowned, while one that still is ran out of time. retry: 0 — ofetch
    // retries a failed GET once by default, which would double the 10s.
    const timer = setTimeout(() => controller.abort(), 10_000)
    const disowned = () => previewFetch?.controller !== controller
    try {
      const posts = await $api<DiscoverPost[]>('/discover/posts', {
        query: { feed_url: feedUrl },
        signal: controller.signal,
        retry: 0,
      })
      if (disowned()) return
      previews.value = {
        ...previews.value,
        [feedUrl]: posts.length ? { status: 'ready', posts } : { status: 'empty' },
      }
      if (posts.length) openPreview(candidate)
    }
    catch (failure) {
      // our own cancel, not the feed's failure — the button is already back to Idle
      if (disowned()) return
      previews.value = {
        ...previews.value,
        [feedUrl]: { status: 'error', detail: detailOf(failure, 'Couldn\'t load that feed.') },
      }
    }
    finally {
      clearTimeout(timer)
      if (!disowned()) previewFetch = null
    }
  }

  // On the phone the preview is the next step, and only from the results: an
  // answer landing after the user moved on must not yank them back.
  function openPreview(candidate: FeedCandidate) {
    if (!isDesktopNow()) {
      if (step.value !== 'input') return
      direction.value = 'forward'
      step.value = 'preview'
    }
    previewing.value = candidate
  }

  function closePreview() {
    previewing.value = null
  }

  // What both preview hosts (the phone's step, the desktop pane) show and say,
  // derived once here so the two never drift apart.
  const previewPosts = computed(() => {
    const open = previewing.value && previews.value[previewing.value.feed_url]
    return open && open.status === 'ready' ? open.posts : []
  })
  // Anything the wizard is waiting on — a search, a preview, an add — for the
  // spinner in its header (ui/Spinner.vue), next to what you're working on.
  const busy = computed(() => loading.value || adding.value
    || Object.values(previews.value).some(entry => entry.status === 'loading'))
  // Pointed at a feed, adding commits straight into it — so say which.
  const previewAddLabel = computed(() => {
    const into = target.value && feedsStore.feeds.find(feed => feed.uid === target.value)
    return into ? `Add to ${into.name}` : 'Add feed'
  })

  // A result's card, the phone preview's docked button and the desktop preview's
  // + all land here. Pointed at a feed, it commits straight into it and answers
  // with that feed's uid (or null on a refusal); otherwise it moves on to
  // Destination and answers null. An open desktop preview stays beside it.
  async function pick(candidate: FeedCandidate): Promise<string | null> {
    if (adding.value) return null
    cancelPreviewFetch()
    picked.value = candidate
    error.value = null
    if (target.value) return addTo(target.value)
    direction.value = 'forward'
    step.value = 'destination'
    return null
  }

  // Every add awaits and answers with the feed it landed in, or null: the host
  // only closes on success — and then opens that feed — because a URL that
  // isn't a feed comes back as a 422 the step has to show.
  async function run(work: (candidate: FeedCandidate) => Promise<string>, fallback: string): Promise<string | null> {
    const candidate = picked.value
    if (!candidate || adding.value) return null
    adding.value = true
    error.value = null
    try {
      return await work(candidate)
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
    return run(async (candidate) => {
      await feedsStore.addSource(feedUid, candidate)
      return feedUid
    }, 'Couldn\'t add that source.')
  }

  // A new feed holding the pick. A blank name or description takes the source's
  // own (the backend's default). Leaving the origin feed comes second, once the
  // new feed holds the source, so it is never briefly in no feed at all.
  function addToNewFeed(input: { name: string, description: string, removeFromOrigin: boolean }) {
    return run(async (candidate) => {
      const feed = await feedsStore.addFeed({ name: input.name, description: input.description, candidate })
      const from = origin.value
      if (input.removeFromOrigin && from) feedsStore.removeSource(from.feedUid, from.sourceUid)
      return feed.uid
    }, 'Couldn\'t create that feed.')
  }

  // Straight to the name step with a source the user already follows, no
  // search: the opener resets the wizard first, like the feed page's Add source.
  function startOwnFeed(feed: Feed, source: Source) {
    picked.value = {
      name: source.name,
      type: source.type,
      site_url: source.site_url,
      feed_url: source.feed_url,
      icon: source.icon,
      subscribers: null,
      already_subscribed: true,
    }
    origin.value = { feedUid: feed.uid, sourceUid: source.uid, feedName: feed.name }
    direction.value = 'forward'
    step.value = 'new-feed'
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
    else if (step.value === 'preview') {
      previewing.value = null
      step.value = 'input'
    }
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
    picked.value = null
    clearPreviews()
    direction.value = 'forward'
    target.value = null
    origin.value = null
  }

  return { step, type, query, loading, results, searched, adding, busy, error, picked, previews, previewing, previewPosts, previewAddLabel, direction, target, origin, selectType, search, preview, closePreview, pick, addTo, addToNewFeed, startOwnFeed, goToNewFeed, back, reset }
}
