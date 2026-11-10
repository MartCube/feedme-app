import type { CSSProperties } from 'vue'

// How long a finger rests on a row before it lifts. Long enough that a tap or
// the start of a scroll never trips it, short enough not to feel like waiting.
const HOLD_MS = 400
// A finger that travels this far before the hold ends was scrolling: let go.
const TOUCH_SLOP = 8
// A mouse lifts the row as soon as it moves this far with the button down; a
// click that doesn't move still opens the feed.
const MOUSE_SLOP = 4
// Holding the row this close to the list's top or bottom edge scrolls it, by
// SCROLL_STEP px a frame.
const EDGE = 48
const SCROLL_STEP = 8
// The lifted row grows a touch, so it reads as picked up.
const LIFT_SCALE = 1.03

// Press-and-drag reordering for one vertical list: hold on touch, drag with a
// mouse, no edit mode. The rows don't move in the DOM while dragging — the
// lifted one follows the pointer and the ones it passes slide aside by
// transform — so the list's keyed order only changes once, on drop, through
// `move(uid, to)`. Generic on purpose (it knows uids and elements, not feeds),
// so the gesture's state machine stays out of the list's template.
export function useDragReorder(uids: () => string[], move: (uid: string, to: number) => void) {
  const rows = new Map<string, HTMLElement>()

  const draggingUid = ref<string | null>(null)
  // The lifted row's travel, and the slot it would drop into.
  const offset = ref(0)
  const target = ref(0)
  // One frame with transitions off, so the rows snap to their new DOM places
  // on drop instead of sliding back from their shifted ones.
  const dropping = ref(false)

  let pending: string | null = null
  let pointerId = -1
  let pointerType = ''
  let startX = 0
  let startY = 0
  let lastY = 0
  let holdTimer: ReturnType<typeof setTimeout> | undefined
  let frame = 0

  // Measured once at lift, in the scroller's content coordinates, so
  // auto-scrolling mid-drag doesn't throw the slots off.
  let from = 0
  let mids: number[] = []
  let pitch = 0
  // Set at lift: the composable also runs during SSR, where there's no document.
  let scroller: HTMLElement | null = null
  let startScroll = 0

  function setRow(uid: string) {
    return (el: unknown) => {
      if (el instanceof HTMLElement) rows.set(uid, el)
      else rows.delete(uid)
    }
  }

  function scrollParent(el: HTMLElement): HTMLElement {
    for (let node = el.parentElement; node; node = node.parentElement) {
      const { overflowY } = getComputedStyle(node)
      if ((overflowY === 'auto' || overflowY === 'scroll') && node.scrollHeight > node.clientHeight) return node
    }
    return (document.scrollingElement as HTMLElement | null) ?? document.documentElement
  }

  function onPointerdown(event: PointerEvent, uid: string) {
    if (event.button !== 0 || draggingUid.value || pending) return
    pending = uid
    pointerId = event.pointerId
    pointerType = event.pointerType
    startX = event.clientX
    startY = lastY = event.clientY
    window.addEventListener('pointermove', onPointermove)
    window.addEventListener('pointerup', onPointerup)
    window.addEventListener('pointercancel', cancel)
    if (pointerType !== 'mouse') holdTimer = setTimeout(lift, HOLD_MS)
  }

  function onPointermove(event: PointerEvent) {
    if (event.pointerId !== pointerId) return
    lastY = event.clientY
    if (draggingUid.value) return update()
    const moved = Math.hypot(event.clientX - startX, event.clientY - startY)
    if (pointerType === 'mouse') {
      if (moved > MOUSE_SLOP) lift()
    }
    else if (moved > TOUCH_SLOP) {
      cancel()
    }
  }

  function lift() {
    const order = uids()
    from = pending ? order.indexOf(pending) : -1
    const el = pending ? rows.get(pending) : undefined
    if (from < 0 || !el) return cancel()

    scroller = scrollParent(el)
    startScroll = scroller.scrollTop
    mids = order.map((uid) => {
      const rect = rows.get(uid)?.getBoundingClientRect()
      return rect ? rect.top + rect.height / 2 + startScroll : 0
    })
    // Row height plus the gap: what each passed row slides by.
    pitch = order.length > 1 ? Math.abs((mids[1] ?? 0) - (mids[0] ?? 0)) : el.offsetHeight

    draggingUid.value = pending
    target.value = from
    offset.value = 0
    // The click that ends the gesture would open the feed.
    window.addEventListener('click', swallowClick, { capture: true })
    navigator.vibrate?.(10)
    frame = requestAnimationFrame(tick)
  }

  // Auto-scroll near the edges; runs every frame while lifted so a finger held
  // still at the edge keeps scrolling.
  function tick() {
    if (!scroller) return
    const box = scroller === document.scrollingElement || scroller === document.documentElement
      ? { top: 0, bottom: window.innerHeight }
      : scroller.getBoundingClientRect()
    if (lastY < box.top + EDGE) scroller.scrollTop -= SCROLL_STEP
    else if (lastY > box.bottom - EDGE) scroller.scrollTop += SCROLL_STEP
    update()
    frame = requestAnimationFrame(tick)
  }

  function update() {
    if (!scroller) return
    offset.value = lastY - startY + scroller.scrollTop - startScroll
    const mid = (mids[from] ?? 0) + offset.value
    target.value = mids.filter((m, i) => i !== from && m < mid).length
  }

  function onPointerup(event: PointerEvent) {
    if (event.pointerId !== pointerId) return
    const uid = draggingUid.value
    const to = target.value
    const moved = uid !== null && to !== from
    stop()
    if (uid === null) return
    // Released inside the click that follows; drop the swallow after it.
    setTimeout(() => window.removeEventListener('click', swallowClick, { capture: true }))
    dropping.value = true
    if (moved) move(uid, to)
    requestAnimationFrame(() => requestAnimationFrame(() => {
      dropping.value = false
    }))
  }

  function cancel() {
    const wasDragging = draggingUid.value !== null
    stop()
    if (wasDragging) {
      dropping.value = true
      window.removeEventListener('click', swallowClick, { capture: true })
      requestAnimationFrame(() => {
        dropping.value = false
      })
    }
  }

  function stop() {
    clearTimeout(holdTimer)
    cancelAnimationFrame(frame)
    window.removeEventListener('pointermove', onPointermove)
    window.removeEventListener('pointerup', onPointerup)
    window.removeEventListener('pointercancel', cancel)
    pending = null
    pointerId = -1
    draggingUid.value = null
    offset.value = 0
  }

  function swallowClick(event: MouseEvent) {
    event.preventDefault()
    event.stopPropagation()
  }

  // Bound on the row, never passive: once a row is lifted, the finger's moves
  // must drag it, not scroll the page. It has to be on the row from the start —
  // a listener added mid-gesture can't stop a scroll the browser already owns.
  function onTouchmove(event: TouchEvent) {
    if (draggingUid.value) event.preventDefault()
  }

  // A long press on Android opens the link's context menu; on a row that's
  // being held, the hold is ours.
  function onContextmenu(event: Event) {
    if (pending || draggingUid.value) event.preventDefault()
  }

  function rowStyle(uid: string): CSSProperties | undefined {
    if (dropping.value) return { transition: 'none' }
    if (!draggingUid.value) return undefined
    if (uid === draggingUid.value) {
      return { transform: `translateY(${offset.value}px) scale(${LIFT_SCALE})`, transition: 'none', zIndex: 10 }
    }
    const i = uids().indexOf(uid)
    let shift = 0
    if (from < target.value && i > from && i <= target.value) shift = -pitch
    else if (target.value < from && i >= target.value && i < from) shift = pitch
    return shift ? { transform: `translateY(${shift}px)` } : undefined
  }

  onScopeDispose(() => {
    stop()
    window.removeEventListener('click', swallowClick, { capture: true })
  })

  return { draggingUid, setRow, rowStyle, onPointerdown, onTouchmove, onContextmenu }
}
