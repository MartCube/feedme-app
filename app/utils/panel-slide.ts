// The push/pop rule for sliding panels and the CSS variables that carry it.
// Shared by the settings sheet (settings/Drawer.vue), the reader pages
// (middleware/page-slide.global.ts) and the add wizard (add/Steps.vue — which supplies its own
// direction from the wizard rather than from the path, so it uses the vars half
// only).
export type PanelSlide = 'push' | 'pop' | 'none'

const depth = (path: string) => path.split('/').filter(Boolean).length

// Deeper pushes in from the right, shallower pops back out. Equal depth is a
// SIDEWAYS move — one feed's page to another's, one settings panel to its
// sibling — and gets no slide: animating it would claim a hierarchy change that
// didn't happen, and it read as a false "you went deeper" push before.
export function panelSlideDirection(to: string, from: string): PanelSlide {
  const d = depth(to) - depth(from)
  if (d === 0) return 'none'
  return d < 0 ? 'pop' : 'push'
}

// Direction rides live CSS variables under a FIXED transition name
// (.panel-slide-* and the .slide-panels defaults live in assets/css/
// transitions.css). Switching the transition NAME doesn't work: Vue binds leave
// hooks to the name a panel *entered* under, so the leaving panel would animate
// with a stale direction, or not at all. Variables are read when the leave
// actually runs.
export function panelSlideVars(slide: PanelSlide) {
  if (slide === 'pop') {
    return { '--panel-duration': 'var(--duration-slide)', '--panel-enter-from': '-25%', '--panel-leave-to': '100%', '--panel-leave-z': '1' }
  }
  if (slide === 'push') {
    return { '--panel-duration': 'var(--duration-slide)', '--panel-enter-from': '100%', '--panel-leave-to': '-25%', '--panel-enter-z': '1' }
  }
  return {}
}
