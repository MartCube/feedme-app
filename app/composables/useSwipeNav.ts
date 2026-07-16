import type { CSSProperties, Ref } from 'vue'

const SNAP_MS = 200
// Resistance factor once the finger drags past the commit threshold.
const OVERDRAG = 0.2

// Swipe right anywhere on a page to pop back to its parent route (navigation
// is hierarchical, not history-based). Rides on VueUse's useSwipe (touch-only,
// passive), so native vertical scrolling keeps working; an axis lock makes
// sure a gesture that starts vertical never drags the page horizontally.
//
// The caller binds `style` on the page root — the same element the page/panel
// transition animates, which is why the inline transform is cleared before
// navigateTo: it would otherwise override the leave-transition's transform and
// freeze the outgoing page.
export function useSwipeBack(target: Ref<HTMLElement | null>, backTo: string | (() => string)) {
  const TRIGGER = 72
  const style = ref<CSSProperties>({})
  let axis: 'x' | 'y' | null = null
  let snapTimer: ReturnType<typeof setTimeout> | undefined

  const { direction, lengthX } = useSwipe(target, {
    threshold: 16,
    onSwipeStart() {
      clearTimeout(snapTimer)
      style.value = {}
    },
    onSwipe() {
      axis ??= direction.value === 'left' || direction.value === 'right' ? 'x' : 'y'
      if (axis !== 'x') return
      // lengthX is start.x − end.x, so a right swipe is negative.
      const drag = -lengthX.value
      if (drag <= 0) {
        style.value = {}
        return
      }
      const offset = Math.min(drag, TRIGGER) + Math.max(drag - TRIGGER, 0) * OVERDRAG
      style.value = { transform: `translateX(${offset}px)` }
    },
    onSwipeEnd() {
      const commit = axis === 'x' && -lengthX.value >= TRIGGER
      axis = null
      if (commit) {
        style.value = {}
        navigateTo(typeof backTo === 'function' ? backTo() : backTo)
      }
      else if (style.value.transform) {
        style.value = { transform: 'translateX(0)', transition: `transform ${SNAP_MS}ms ease-out` }
        snapTimer = setTimeout(() => {
          style.value = {}
        }, SNAP_MS)
      }
    },
  })

  onScopeDispose(() => clearTimeout(snapTimer))

  return { style }
}
