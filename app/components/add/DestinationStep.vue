<script setup lang="ts">
const emit = defineEmits<{ back: [], close: [], choose: [feedUid: string], newFeed: [] }>()

const { feeds } = storeToRefs(useFeedsStore())

const { picked, adding, error, busy } = useAddFeedWizard()
</script>

<template>
  <!-- touch-none lets vaul own the drag-to-close gesture; revisit once the
       destination list needs real touch scrolling. -->
  <div class="flex h-full touch-none flex-col scroll-host bg-default page-inset *:max-w-reading">
    <header class="flex items-center gap-xs">
      <IconButton
        icon="i-ph-x-bold"
        aria-label="Close add feed"
        @click="emit('close')"
      />
      <IconButton
        icon="i-ph-caret-left-bold"
        aria-label="Back"
        @click="emit('back')"
      />
    </header>

    <!-- The one source being added names the question; the cards below answer
         it. Wraps rather than truncating — a long name is still the context. -->
    <h1 class="mt-lg text-title tracking-tight">
      Add {{ picked?.name }} to<Spinner
        :active="busy"
        class="ms-sm align-middle"
      />
    </h1>

    <!-- Above the destination list, not below it: this panel is touch-none (vaul owns
         the gesture), so anything under a long feed list is unreachable on mobile —
         and a failure that can't be read is a failure that looks like nothing happened. -->
    <p
      v-if="error"
      class="mt-xs text-caption text-error text-inset"
    >
      {{ error }}
    </p>

    <!-- New feed first: it's the common case for a first source, and the one
         row that's always there. Tapping a feed commits: the source joins it and
         the wizard closes. -->
    <ul class="mt-md flex flex-col gap-sm">
      <li>
        <button
          type="button"
          :disabled="adding"
          class="flex w-full items-center gap-sm rounded-2xl bg-elevated p-sm text-left shadow-elevated transition-colors"
          :class="adding ? 'text-dimmed' : 'hover-lift'"
          @click="emit('newFeed')"
        >
          <UIcon
            name="i-ph-plus-bold"
            class="size-5 shrink-0"
            :class="adding ? 'text-dimmed' : 'text-muted'"
          />
          <span class="text-body">New feed</span>
        </button>
      </li>
      <li
        v-for="feed in feeds"
        :key="feed.uid"
      >
        <button
          type="button"
          :disabled="adding"
          class="flex w-full items-center gap-sm rounded-2xl bg-elevated p-sm text-left shadow-elevated transition-colors"
          :class="!adding && 'hover-lift'"
          :aria-label="`Add to ${feed.name}`"
          @click="emit('choose', feed.uid)"
        >
          <span
            class="flex min-w-0 flex-1 items-baseline gap-xs"
            :class="adding && 'text-dimmed'"
          >
            <span class="min-w-0 truncate text-body">{{ feed.name }}</span>
            <span :class="adding ? 'text-caption' : 'text-caption text-muted'">{{ feed.sources.length }}</span>
          </span>
        </button>
      </li>
    </ul>
  </div>
</template>
