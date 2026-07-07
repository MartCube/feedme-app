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
