import type { FeedType } from '~/assets/types'

// Single source for the wizard's feed types: the type step renders its cards
// from it, and the search step looks up its heading label/icon and input
// placeholder by the chosen type. placeholder stays a separate field because
// website's search prompt differs from its card hint.
export const feedTypes: { type: FeedType, label: string, hint: string, placeholder: string, icon: string }[] = [
  { type: 'website', label: 'Website', hint: 'Any site or RSS feed', placeholder: 'Paste a link or search…', icon: 'i-ph-globe-bold' },
  { type: 'youtube', label: 'YouTube', hint: 'Channels by link or search', placeholder: 'Channels by link or search', icon: 'i-ph-youtube-logo-bold' },
  { type: 'reddit', label: 'Reddit', hint: 'Subreddits by link or search', placeholder: 'Subreddits by link or search', icon: 'i-ph-reddit-logo-bold' },
]
