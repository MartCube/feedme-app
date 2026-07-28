<script setup lang="ts">
import type { FeedType } from '~/assets/types'

// The route-driven edit panels (folder / source / scoped add / confirm),
// switched by /edit/* route — no nested NuxtPage. Hosted by the mobile bottom
// sheet (edit/Drawer.vue) and the desktop content page.
//
// One route per panel: /edit/:uid is the base (a folder_* uid → folder panel;
// a loose feed_* uid → source panel directly), /edit/:uid/source/:sourceUid is
// a member source subpage, /edit/:uid/add[/input] is the scoped add flow, and
// the two confirm sheets are /edit/:uid/delete (delete this folder, or this
// source when the uid is a loose feed_*) and /edit/:uid/source/:sourceUid/delete
// (remove that source from the folder).
//
// vue-router's live route, not Nuxt's useRoute(): on desktop these panels
// render without a NuxtPage, where Nuxt's route object never re-syncs.
const router = useRouter()
const route = reactive({
  name: computed(() => router.currentRoute.value.name),
  path: computed(() => router.currentRoute.value.path),
  params: computed(() => router.currentRoute.value.params),
})

const feedsStore = useFeedsStore()
const { folders, feeds } = storeToRefs(feedsStore)
const { folderDeleteImpact, deleteFolder, deleteFeed, removeFromFolder } = feedsStore
const wizard = useAddFeedWizard()

const uid = computed(() => route.params.uid as string)
const sourceUid = computed(() => route.params.sourceUid as string | undefined)

const view = computed(() => {
  switch (route.name) {
    case 'edit-source': return 'source'
    case 'edit-add': return 'add-type'
    case 'edit-add-input': return 'add-input'
    case 'edit-delete':
    case 'edit-source-delete': return 'confirm'
    default: return uid.value?.startsWith('folder_') ? 'folder' : 'loose'
  }
})

const folder = computed(() => folders.value.find(f => f.uid === uid.value))
const baseFeed = computed(() => feeds.value.find(f => f.uid === uid.value))
const sourceFeed = computed(() => feeds.value.find(f => f.uid === sourceUid.value))

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
  // Unlink a member source from the folder it's being edited under.
  if (route.name === 'edit-source-delete') {
    const f = folder.value
    const source = sourceFeed.value
    if (!f || !source) return
    return {
      action: 'Remove source from feed',
      verb: 'Remove',
      subject: source.name,
      context: f.name,
      note: 'It stays subscribed — it moves to your list unless it\'s in another feed.',
      backTo: `/edit/${f.uid}/source/${source.uid}`,
      act: () => {
        removeFromFolder(f.uid, source.uid)
        navigateTo(`/edit/${f.uid}`)
      },
    }
  }
  // Delete the whole feed. Cascades: members in no other folder get
  // unsubscribed, so the note names how many that is.
  if (folder.value) {
    const f = folder.value
    const impact = folderDeleteImpact(f.uid)
    return {
      action: 'Delete feed',
      verb: 'Delete',
      subject: f.name,
      note: impact === 1
        ? '1 source that isn\'t in another feed will be unsubscribed.'
        : impact > 1
          ? `${impact} sources that aren't in another feed will be unsubscribed.`
          : 'Its sources stay subscribed — they\'re in other feeds or the list.',
      backTo: `/edit/${f.uid}`,
      act: () => {
        deleteFolder(f.uid)
        navigateTo('/')
      },
    }
  }
  // Unsubscribe a standalone source.
  if (baseFeed.value) {
    const source = baseFeed.value
    return {
      action: 'Delete source',
      verb: 'Delete',
      subject: source.name,
      note: 'Unsubscribes it everywhere — its posts leave your list.',
      backTo: `/edit/${source.uid}`,
      act: () => {
        deleteFeed(source.uid)
        navigateTo('/')
      },
    }
  }
  return undefined
})

// Same push/pop mechanism as the settings drawer: a FIXED panel-slide
// transition whose direction rides on --panel-* variables (transitions.css).
// Deeper path pushes in from the right, shallower pops back.
const slide = ref<'push' | 'pop' | 'none'>('none')
watch(() => route.path, (to, from) => {
  if (!to.startsWith('/edit/') || !from.startsWith('/edit/')) {
    slide.value = 'none'
    return
  }
  const depth = (path: string) => path.split('/').filter(Boolean).length
  slide.value = depth(to) < depth(from) ? 'pop' : 'push'
})

const slideVars = computed(() => {
  if (slide.value === 'pop') {
    return { '--panel-enter-from': '-25%', '--panel-leave-to': '100%', '--panel-leave-z': '1' }
  }
  if (slide.value === 'push') {
    return { '--panel-enter-from': '100%', '--panel-leave-to': '-25%', '--panel-enter-z': '1' }
  }
  return {}
})

// Scoped add flow: the add step components are reused as extra panels, but
// destination is already known (this folder) so DestinationStep is skipped.
function onAddSelect(type: FeedType) {
  wizard.selectType(type)
  navigateTo(`/edit/${uid.value}/add/input`)
}

function onAddCommit() {
  if (!wizard.selectedFeeds.value.length) return
  wizard.chooseDestination(uid.value)
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
        :key="route.path"
        :folder="folder"
      />
      <EditSourcePanel
        v-else-if="view === 'source' && sourceFeed"
        :key="route.path"
        :feed="sourceFeed"
        :folder-uid="uid"
      />
      <EditSourcePanel
        v-else-if="view === 'loose' && baseFeed"
        :key="route.path"
        :feed="baseFeed"
      />
      <EditConfirmPanel
        v-else-if="view === 'confirm' && confirm"
        :key="route.path"
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
        :key="route.path"
        @select="onAddSelect"
        @close="navigateTo(`/edit/${uid}`)"
      />
      <AddSearchStep
        v-else-if="view === 'add-input'"
        :key="route.path"
        @back="navigateTo(`/edit/${uid}/add`)"
        @forward="onAddCommit"
      />
    </Transition>
  </div>
</template>
