// Drives the .page-slide-* transitions (assets/css/main.css) for the reader
// flow. home → feed → post sit left-to-right, so a deeper route pushes in
// from the right and a shallower one pops back out to the right. Set on route
// meta from middleware — this runs before the page renders, unlike a watch on
// route.path in a component, which updates one navigation too late.
const isReader = (path: string) => path === '/' || path.startsWith('/feed/')
const depth = (path: string) => path.split('/').filter(Boolean).length

export default defineNuxtRouteMiddleware((to, from) => {
  if (to.path === from.path) return
  if (!isReader(to.path) && !isReader(from.path)) return

  const name = isReader(to.path) && isReader(from.path)
    ? (depth(to.path) < depth(from.path) ? 'page-slide-right' : 'page-slide-left')
    // No CSS matches page-none, so the swap is instant — but the Transition
    // wrapper stays mounted, which keeps the next slide from being skipped.
    : 'page-none'

  to.meta.pageTransition = { name }
  from.meta.pageTransition = { name }
})
