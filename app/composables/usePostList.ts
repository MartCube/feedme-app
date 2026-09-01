import type { Post, PostPage } from '~/assets/types'

// The post list behind every reader screen. `uid` is polymorphic — all, saved,
// a saved group, a folder or a single feed — and the backend resolves it in the
// same order the frontend does (backend.md § Endpoint catalog), so there is
// nothing to branch on here.
//
// Cursor-paged, not offset-paged: a feed reader gets new posts inserted at the
// top mid-scroll, which is exactly the case offsets skip and repeat rows on.
const PAGE_SIZE = 10

export function usePostList(uid: MaybeRefOrGetter<string>) {
  const { $api } = useNuxtApp()

  const items = ref<Post[]>([])
  const pending = ref(false)
  const failed = ref(false)
  // No cursor and nothing loaded yet is the start; no cursor after a page is
  // the end of the list.
  const cursor = ref<string | null>(null)
  const done = ref(false)
  // Bumped whenever the uid changes. A page still in flight when that happens
  // belongs to a list nobody is looking at any more — without this it would
  // append the old feed's posts to the new one.
  let generation = 0

  async function loadMore() {
    if (pending.value || done.value) return
    pending.value = true
    const requested = generation
    try {
      const page = await $api<PostPage>(`/feeds/${toValue(uid)}/posts`, {
        query: { limit: PAGE_SIZE, cursor: cursor.value ?? undefined },
      })
      if (requested !== generation) return
      items.value = [...items.value, ...page.items]
      cursor.value = page.next_cursor
      done.value = page.next_cursor === null
      failed.value = false
    }
    catch {
      if (requested !== generation) return
      // Stop paging rather than hammer a server that just refused; the list
      // keeps what it has and says so.
      done.value = true
      failed.value = true
    }
    finally {
      // The newer list owns `pending` — it reset it and started its own page.
      if (requested === generation) pending.value = false
    }
  }

  // A uid change is a different list, not more of this one — on desktop the
  // same component instance stays mounted across feeds.
  watch(() => toValue(uid), () => {
    generation++
    items.value = []
    cursor.value = null
    done.value = false
    failed.value = false
    pending.value = false
    loadMore()
  }, { immediate: true })

  return { items, pending, failed, done, loadMore }
}
