<script setup lang="ts">
import type { FeedType } from '~/assets/types'

// The route-driven edit panels (folder / feed / scoped add / confirm),
// switched by /edit/* route — no nested NuxtPage. Hosted by the mobile bottom
// sheet (edit/Drawer.vue) as one sliding stack, and by the desktop content
// area (desktop/ContentOverlay.vue) as TWO instances side by side: `master`
// renders what /edit/:uid names and `detail` renders whatever deeper segment
// is open beside it, the same master–detail split the reader uses for a feed
// and a post.
//
// One route per panel: /edit/:uid is the base (a folder_* uid → folder panel;
// a loose feed_* uid → feed panel directly), /edit/:uid/feed/:feedUid is a
// member feed subpage, /edit/:uid/add[/input] is the scoped add flow, and the
// two confirm sheets are /edit/:uid/delete (delete this folder, or unsubscribe
// this feed when the uid is a loose feed_*) and /edit/:uid/feed/:feedUid/delete
// (remove that feed from the folder).
//
// 'all' is the mobile sheet: one panel at a time, deepest wins, sliding.
// 'master'/'detail' are the two desktop panes, which never slide — the master
// stays put while the detail swaps, exactly like the post pane.
// 'single' is the desktop pane for a flow with no master to sit beside: a loose
// feed, which has nothing below it to pick. Same views as the sheet, no slide.
const props = withDefaults(defineProps<{ pane?: 'all' | 'single' | 'master' | 'detail' }>(), {
  pane: 'all',
})

// vue-router's live route, not Nuxt's useRoute(): on desktop these panels
// render without a NuxtPage, where Nuxt's route object never re-syncs.
const router = useRouter()
const route = reactive({
  name: computed(() => router.currentRoute.value.name),
  path: computed(() => router.currentRoute.value.path),
  params: computed(() => router.currentRoute.value.params),
})

const feedsStore = useFeedsStore()
const { folders, feeds, loaded, unreachable } = storeToRefs(feedsStore)
const { folderDeleteImpact, deleteFolder, deleteFeed, removeFromFolder } = feedsStore
const wizard = useAddFeedWizard()

const uid = computed(() => route.params.uid as string)
const memberUid = computed(() => route.params.feedUid as string | undefined)

// What /edit/:uid alone names: a folder, or a loose feed edited directly.
const baseView = computed(() => uid.value?.startsWith('folder_') ? 'folder' : 'loose')

// What the segments below it name, if any.
const deepView = computed(() => {
  switch (route.name) {
    case 'edit-feed': return 'member'
    case 'edit-add': return 'add-type'
    case 'edit-add-input': return 'add-input'
    case 'edit-delete':
    case 'edit-feed-delete': return 'confirm'
    default: return undefined
  }
})

// 'all' and 'single' both show the deepest thing the URL names; the two panes
// each show only their own half of it.
const view = computed(() => {
  if (props.pane === 'master') return baseView.value
  if (props.pane === 'detail') return deepView.value
  return deepView.value ?? baseView.value
})

// The master pane is keyed on the entity, not the path, so drilling into a
// member doesn't remount the folder panel and wipe an in-progress draft.
const panelKey = computed(() => props.pane === 'master' ? uid.value : route.path)

const folder = computed(() => folders.value.find(f => f.uid === uid.value))
const baseFeed = computed(() => feeds.value.find(f => f.uid === uid.value))
const memberFeed = computed(() => feeds.value.find(f => f.uid === memberUid.value))

// Every destructive action in the edit flow, side by side: its copy, where
// Cancel goes back to, and the store call it commits. ConfirmPanel just
// renders this.
interface Confirm {
  action: string
  verb: string
  subject: string
  context?: string
  note: string
  backTo: string
  act: () => void
}

const confirm = computed<Confirm | undefined>(() => {
  // Unlink a member feed from the folder it's being edited under.
  if (route.name === 'edit-feed-delete') {
    const f = folder.value
    const member = memberFeed.value
    if (!f || !member) return
    return {
      action: 'Remove from this folder',
      verb: 'Remove',
      subject: member.name,
      context: f.name,
      note: 'It stays subscribed — it moves to your list unless it\'s in another folder.',
      backTo: `/edit/${f.uid}/feed/${member.uid}`,
      act: () => {
        removeFromFolder(f.uid, member.uid)
        navigateTo(`/edit/${f.uid}`)
      },
    }
  }
  // Delete the whole folder. Cascades: members in no other folder get
  // unsubscribed, so the note names how many that is.
  if (folder.value) {
    const f = folder.value
    const impact = folderDeleteImpact(f.uid)
    return {
      action: 'Delete folder',
      verb: 'Delete',
      subject: f.name,
      note: impact === 1
        ? '1 feed that isn\'t in another folder will be unsubscribed.'
        : impact > 1
          ? `${impact} feeds that aren't in another folder will be unsubscribed.`
          : 'Its feeds stay subscribed — they\'re in other folders or the list.',
      backTo: `/edit/${f.uid}`,
      act: () => {
        deleteFolder(f.uid)
        navigateTo('/')
      },
    }
  }
  // Unsubscribe a loose feed.
  if (baseFeed.value) {
    const feed = baseFeed.value
    return {
      action: 'Delete feed',
      verb: 'Delete',
      subject: feed.name,
      note: 'Unsubscribes it everywhere — its posts leave your list.',
      backTo: `/edit/${feed.uid}`,
      act: () => {
        deleteFeed(feed.uid)
        navigateTo('/')
      },
    }
  }
  return undefined
})

// Nothing here to edit: a stale /edit/* link (the folder or feed was deleted, on this
// device or another), or data that never arrived. Every panel below is keyed on finding
// its entity, so the drawer would otherwise sit open and empty with nothing to press —
// send the reader back to the home screen, which knows how to explain itself. Held until
// the store has answered one way or the other, so a deep link doesn't bounce mid-load.
const missing = computed(() => {
  if (!loaded.value && !unreachable.value) return false
  // Exactly one instance owns the redirect. On desktop both panes are mounted
  // at once, and two of them would fire navigateTo('/') for the same stale uid.
  if (props.pane === 'detail') return false
  if (baseView.value === 'folder' && !folder.value) return true
  if (baseView.value === 'loose' && !baseFeed.value) return true
  if (deepView.value === 'member' && !memberFeed.value) return true
  if (deepView.value === 'confirm' && !confirm.value) return true
  return false
})

watch(missing, (gone) => {
  if (gone) navigateTo('/')
}, { immediate: true })

// Push/pop between stacked panels (the rule and the vars: utils/panel-slide.ts).
// Only the mobile sheet stacks them — the desktop panes sit side by side, so
// they stay on the no-motion default and swap instantly.
const slide = ref<PanelSlide>('none')
watch(() => route.path, (to, from) => {
  if (props.pane !== 'all') return
  slide.value = to.startsWith('/edit/') && from.startsWith('/edit/')
    ? panelSlideDirection(to, from)
    : 'none'
})

const slideVars = computed(() => panelSlideVars(slide.value))

// Scoped add flow: the add step components are reused as extra panels, but
// destination is already known (this folder) so DestinationStep is skipped.
function onAddSelect(type: FeedType) {
  wizard.selectType(type)
  navigateTo(`/edit/${uid.value}/add/input`)
}

async function onAddCommit() {
  if (!wizard.selectedFeeds.value.length) return
  if (!await wizard.chooseDestination(uid.value)) return
  wizard.reset()
  navigateTo(`/edit/${uid.value}`)
}
</script>

<template>
  <div
    class="slide-panels h-full"
    :style="slideVars"
  >
    <Transition name="panel-slide">
      <EditFolderPanel
        v-if="view === 'folder' && folder"
        :key="panelKey"
        :folder="folder"
        :active-uid="memberUid"
      />
      <EditFeedPanel
        v-else-if="view === 'member' && memberFeed"
        :key="panelKey"
        :feed="memberFeed"
        :folder-uid="uid"
      />
      <EditFeedPanel
        v-else-if="view === 'loose' && baseFeed"
        :key="panelKey"
        :feed="baseFeed"
      />
      <EditConfirmPanel
        v-else-if="view === 'confirm' && confirm"
        :key="panelKey"
        :action="confirm.action"
        :verb="confirm.verb"
        :subject="confirm.subject"
        :context="confirm.context"
        :note="confirm.note"
        :back-to="confirm.backTo"
        @confirm="confirm.act()"
      />
      <AddTypeStep
        v-else-if="view === 'add-type'"
        :key="panelKey"
        @select="onAddSelect"
        @close="navigateTo(`/edit/${uid}`)"
      />
      <AddSearchStep
        v-else-if="view === 'add-input'"
        :key="panelKey"
        @back="navigateTo(`/edit/${uid}/add`)"
        @forward="onAddCommit"
      />
    </Transition>
  </div>
</template>
