// Press-and-hold on a home feed row to open its edit drawer (mobile's twin of
// the desktop hover 3-dot). Manual pointer handling rather than VueUse's
// onLongPress because the rows are a v-for (no per-element ref) and, more
// importantly, we must suppress the click that follows the hold so the row's
// NuxtLink doesn't also navigate to the feed. A small move cancels it so
// vertical scrolling is untouched.
const DELAY = 450
const MOVE_CANCEL = 10

export function useLongPress(onLong: (uid: string) => void) {
  let timer: ReturnType<typeof setTimeout> | undefined
  let firedUid: string | null = null
  let startX = 0
  let startY = 0

  function start(uid: string, e: PointerEvent) {
    firedUid = null
    startX = e.clientX
    startY = e.clientY
    clearTimeout(timer)
    timer = setTimeout(() => {
      firedUid = uid
      onLong(uid)
    }, DELAY)
  }

  function move(e: PointerEvent) {
    if (timer && (Math.abs(e.clientX - startX) > MOVE_CANCEL || Math.abs(e.clientY - startY) > MOVE_CANCEL)) {
      cancel()
    }
  }

  function cancel() {
    clearTimeout(timer)
    timer = undefined
  }

  // Runs in the capture phase (before NuxtLink's own click handler) so
  // preventDefault stops the navigation that would otherwise follow the hold.
  function onClick(uid: string, e: MouseEvent) {
    if (firedUid === uid) {
      e.preventDefault()
      e.stopPropagation()
      firedUid = null
    }
  }

  onScopeDispose(cancel)

  return { start, move, cancel, onClick }
}
