import type { Post, SavedGroupName } from '~/assets/types'

// Where a plain Save lands. The spec (screens-and-flows.md) makes Save a
// toggle, not a chooser; the three groups exist and are readable, but nothing
// picks between them yet.
const DEFAULT_GROUP: SavedGroupName = 'bookmarks'

// One post, by uid, plus its save toggle. Owned by whichever host has the uid —
// the mobile post page or the desktop shell — which then passes the post down
// to FeedPostView. One fetch per layout, and no cache shared between components
// that mount and unmount independently: the mobile tree and the desktop shell
// swap places at the lg breakpoint, and a shared useAsyncData entry gets
// cleared out from under the survivor exactly there.
export function usePost(uid: MaybeRefOrGetter<string | null>) {
  const { $api } = useNuxtApp()

  const post = ref<Post | null>(null)
  const failed = ref(false)
  const saved = computed(() => Boolean(post.value?.saved_group))
  const saving = ref(false)

  watch(() => toValue(uid), async (current) => {
    post.value = null
    failed.value = false
    // Nothing open — the desktop detail pane is empty until a post is picked.
    if (!current) return
    try {
      const result = await $api<Post>(`/posts/${current}`)
      // A second navigation while this one was in flight owns the pane now.
      if (toValue(uid) === current) post.value = result
    }
    catch {
      if (toValue(uid) === current) failed.value = true
    }
  }, { immediate: true })

  async function toggleSave() {
    if (!post.value || saving.value) return
    saving.value = true
    const path = `/posts/${post.value.uid}/save`
    try {
      if (saved.value) {
        // Idempotent server-side, so a double tap is harmless.
        await $api(path, { method: 'DELETE' })
        post.value = { ...post.value, saved_group: null }
      }
      else {
        // An upsert: moving between groups, when there's UI for it, is this
        // same call.
        const result = await $api<{ group: SavedGroupName }>(path, {
          method: 'PUT',
          body: { group: DEFAULT_GROUP },
        })
        post.value = { ...post.value, saved_group: result.group }
      }
    }
    finally {
      saving.value = false
    }
  }

  return { post, failed, saved, saving, toggleSave }
}
