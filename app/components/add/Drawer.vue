<script setup lang="ts">
// Hosts the add-feed bottom sheet. Like the settings drawer, the /add URL
// renders the home page component (see the pages:extend hook in nuxt.config)
// so the feed list stays mounted behind the sheet; this component just opens
// the drawer on /add and routes home when it closes.
const route = useRoute()
const open = ref(false)

const onAdd = computed(() => route.path === '/add')

// vaul emits animationEnd(false) for its initial closed state — only a close
// that follows a completed open animation should navigate home.
const hasOpened = ref(false)

watch(onAdd, (on) => {
  open.value = on
})

onMounted(() => {
  if (onAdd.value) {
    open.value = true
  }
})

function close() {
  open.value = false
}

function onAnimationEnd(isOpen: boolean) {
  if (isOpen) {
    hasOpened.value = true
  }
  else if (hasOpened.value && onAdd.value) {
    navigateTo('/')
  }
}

// Rough static results — no search logic. This screen is a visual
// demonstration only: an input, then a list of results with an add
// affordance. Wiring (real search + add to feed list / group) is a later task.
const results = [
  { name: 'Vue.js on Medium', url: 'medium.com/vuejs', icon: 'i-ph-globe-bold' },
  { name: 'Vue Mastery', url: 'vuemastery.com', icon: 'i-ph-globe-bold' },
  { name: 'Fireship', url: 'youtube.com/@fireship', icon: 'i-ph-youtube-logo-bold' },
  { name: 'r/vuejs', url: 'reddit.com/r/vuejs', icon: 'i-ph-reddit-logo-bold' },
]
</script>

<template>
  <UDrawer
    v-model:open="open"
    :handle="false"
    :ui="{
      // overflow-hidden clips the panel to the sheet's rounded top corners.
      content: 'mt-0 h-full max-h-full overflow-hidden',
      container: 'grow gap-0 p-0 overflow-hidden',
      body: 'relative overflow-hidden',
    }"
    @animation-end="onAnimationEnd"
  >
    <template #body>
      <!-- touch-none lets vaul own the drag-to-close gesture; revisit once the
           results list needs real touch scrolling. -->
      <div class="h-full touch-none overflow-y-auto bg-default px-8 pt-6 pb-12">
        <IconButton
          icon="i-ph-x-bold"
          aria-label="Close add feed"
          @click="close"
        />

        <h1 class="mt-10 text-title tracking-tight">
          Add feed
        </h1>

        <UInput
          icon="i-ph-magnifying-glass-bold"
          placeholder="Add a feed…"
          size="xl"
          class="mt-6 w-full"
        />

        <ul class="mt-4 flex flex-col">
          <li
            v-for="result in results"
            :key="result.url"
            class="flex items-center gap-3 py-3"
          >
            <UIcon
              :name="result.icon"
              class="size-6 shrink-0 text-muted"
            />
            <div class="min-w-0 flex-1">
              <p class="truncate text-body">
                {{ result.name }}
              </p>
              <p class="truncate text-caption text-muted">
                {{ result.url }}
              </p>
            </div>
            <IconButton
              icon="i-ph-plus-bold"
              size="sm"
              aria-label="Add feed"
            />
          </li>
        </ul>
      </div>
    </template>
  </UDrawer>
</template>
