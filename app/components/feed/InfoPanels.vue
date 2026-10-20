<script setup lang="ts">
// Which feed-page view a /feed/:uid/info/… path names, rendered with what it
// needs. One switch for both hosts: the mobile page (pages/feed/[uid]/info)
// and, on desktop, the post pane whenever no post is open — so a view looks
// and behaves the same in either.
const props = defineProps<{ uid: string, rest: string[] }>()

const feedsStore = useFeedsStore()
const { feeds, loaded, unreachable } = storeToRefs(feedsStore)

const view = computed(() => infoView(props.rest))
const back = computed(() => infoBack(props.uid, props.rest))

const feed = computed(() => feeds.value.find(f => f.uid === props.uid))
const source = computed(() => feed.value?.sources.find(s => s.uid === props.rest[1]))

// Nothing here to show: a stale link — the feed was deleted, or the source
// left it, on this device or another. Back to the post list, which knows how
// to explain itself; held until /home has answered, so a deep link doesn't
// bounce mid-load.
const missing = computed(() => {
  if (!loaded.value && !unreachable.value) return false
  // Home and Saved have no page of their own, so their info links are dead too
  if (!feed.value) return true
  return (view.value === 'source' || view.value === 'remove') && !source.value
})
watch(missing, (gone) => {
  if (gone) navigateTo(feed.value ? `/feed/${props.uid}/info` : '/')
}, { immediate: true })

function deleteFeed() {
  feedsStore.deleteFeed(props.uid)
  navigateTo('/')
}

function removeSource() {
  if (!source.value) return
  feedsStore.removeSource(props.uid, source.value.uid)
  navigateTo(`/feed/${props.uid}/info`)
}
</script>

<template>
  <FeedInfoEdit
    v-if="view === 'edit' && feed"
    :feed="feed"
    :back="back"
  />
  <FeedConfirm
    v-else-if="view === 'delete' && feed"
    action="Delete feed"
    verb="Delete"
    :subject="feed.name"
    note="Its sources leave your list unless another feed has them. Saved posts stay."
    :back-to="back"
    @confirm="deleteFeed"
  />
  <FeedSourceEdit
    v-else-if="view === 'source' && feed && source"
    :feed="feed"
    :source="source"
    :back="back"
  />
  <FeedConfirm
    v-else-if="view === 'remove' && feed && source"
    action="Remove from this feed"
    verb="Remove"
    :subject="source.name"
    :context="feed.name"
    note="It stays in your other feeds. Saved posts stay."
    :back-to="back"
    @confirm="removeSource"
  />
  <FeedInfo
    v-else
    :uid="uid"
    :feed="feed"
    :back="back"
  />
</template>
