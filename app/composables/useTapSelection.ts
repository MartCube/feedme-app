// Brief "you tapped this" highlight for list rows (feeds, posts). On mobile it
// flashes the elevated card treatment on the tapped item so the tap registers
// before the page slides away. Desktop will reuse selectedUid as a persistent
// master–detail selection; for now it self-clears.
export function useTapSelection() {
  const selectedUid = ref<string | null>(null)
  let timer: ReturnType<typeof setTimeout> | undefined

  function select(uid: string) {
    selectedUid.value = uid
    clearTimeout(timer)
    // Outlast the 0.35s page-slide (transitions.css) so the item stays lit
    // through the leave animation.
    timer = setTimeout(() => {
      selectedUid.value = null
    }, 450)
  }

  onScopeDispose(() => clearTimeout(timer))

  return { selectedUid, select }
}
