import type { Post, PostPage } from '~/assets/types'

// The post list behind every reader screen. `uid` is polymorphic — all, saved,
// a saved group or a feed — and the backend resolves it in the
// same order the frontend does (backend.md § Endpoint catalog), so there is
// nothing to branch on here.
//
// Cursor-paged, not offset-paged: a feed reader gets new posts inserted at the
// top mid-scroll, which is exactly the case offsets skip and repeat rows on.
//
// An optional `q` narrows the same list: GET /search takes the uid as its
// `scope` and answers the identical page shape, so searching is a different URL
// and nothing else — same cursor, same items, same failure rules. That is why
// there is no second composable for it.
//
// `contents` is what the uid currently stands for — the caller's say on when
// the same uid means different posts (a source switched off, or added). It's
// only compared, never sent: a change resets the list like a new uid does.
const PAGE_SIZE = 10

export function usePostList(uid: MaybeRefOrGetter<string>, q?: MaybeRefOrGetter<string>, contents?: MaybeRefOrGetter<string>) {
  const { $api } = useNuxtApp()

  const term = () => toValue(q)?.trim() ?? ''

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
      const paging = { limit: PAGE_SIZE, cursor: cursor.value ?? undefined }
      const searching = term()
      const page = searching
        ? await $api<PostPage>('/search', {
            query: { q: searching, scope: toValue(uid), ...paging },
          })
        : await $api<PostPage>(`/feeds/${toValue(uid)}/posts`, { query: paging })
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
  // same component instance stays mounted across feeds. A changed query or
  // changed contents are the same kind of event, so they reset identically;
  // the generation counter above is what discards a page still in flight for
  // the term you just stopped typing.
  watch([() => toValue(uid), term, () => toValue(contents)], () => {
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
