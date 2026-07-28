// Single source of the mobile ↔ desktop breakpoint: Tailwind `lg`, 1024px.
// (`lg` here is the BREAKPOINT prefix — not the `lg` spacing token.)
export const DESKTOP_MQ = '(min-width: 64rem)'

// Hydration-safe reactive check: false during SSR and the hydration render,
// flips right after mount on wide clients. Drives the layout's single
// mobile-tree / desktop-shell branch. The useMounted gate is load-bearing:
// bare useMediaQuery reads matchMedia during the hydration render, and the
// resulting server/client mismatch leaves the DOM stuck with the server's
// (mobile) classes — an invisible desktop shell.
export function useIsDesktop() {
  const mounted = useMounted()
  const matches = useMediaQuery(DESKTOP_MQ)
  return computed(() => mounted.value && matches.value)
}

// Synchronous check for imperative guards that run before the reactive ref
// flips (e.g. a drawer host's onMounted during a desktop deep-load of
// /settings/*). Always false on the server.
export function isDesktopNow() {
  return import.meta.client && window.matchMedia(DESKTOP_MQ).matches
}
