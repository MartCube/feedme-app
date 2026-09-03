// Drives the .page-slide-* transitions (assets/css/transitions.css) for the
// reader flow. home → feed → post sit left-to-right, so a deeper route pushes
// in from the right and a shallower one pops back out to the right. Set on
// route meta from middleware — this runs before the page renders, unlike a
// watch on route.path in a component, which updates one navigation too late.
//
// The depth rule itself is utils/panel-slide.ts, shared with the drawer
// panels; this map is only the reader flow's name for each direction.
const isReader = (path: string) => path === '/' || path.startsWith('/feed/')

// No CSS matches page-none, so the swap is instant — but the Transition wrapper
// stays mounted, which keeps the next slide from being skipped.
const PAGE_SLIDE: Record<PanelSlide, string> = {
  push: 'page-slide-left',
  pop: 'page-slide-right',
  none: 'page-none',
}

export default defineNuxtRouteMiddleware((to, from) => {
  if (to.path === from.path) return
  if (!isReader(to.path) && !isReader(from.path)) return

  const name = isReader(to.path) && isReader(from.path)
    ? PAGE_SLIDE[panelSlideDirection(to.path, from.path)]
    : 'page-none'

  to.meta.pageTransition = { name }
  from.meta.pageTransition = { name }
})
