<script setup lang="ts">
// The phone's feed preview: a step of its own between the results and
// Destination, because on a phone the posts list sits behind the drawer. Only
// entered once posts have arrived (the result's Preview button carried the
// wait), so it has no loading state. Add does exactly what tapping the result
// does.
const emit = defineEmits<{ back: [], close: [], add: [] }>()

const wizard = useAddFeedWizard()
const { previewing, previewPosts, previewAddLabel, adding, error, busy } = wizard
</script>

<template>
  <!-- The only wizard panel that scrolls by touch: ten posts don't fit, so the
       list pans vertically and vaul still takes a drag-down at the top. The
       docked button sits below the scroll, not over it, so the last card's xl
       runway clears it without extra room. -->
  <div class="flex h-full flex-col bg-default">
    <div class="flex-1 touch-pan-y scroll-host page-inset *:max-w-reading">
      <header class="flex items-center gap-xs">
        <IconButton
          icon="i-ph-x-bold"
          aria-label="Close add feed"
          @click="emit('close')"
        />
        <IconButton
          icon="i-ph-caret-left-bold"
          aria-label="Back to results"
          @click="emit('back')"
        />
        <IconButton
          v-if="previewing?.site_url"
          icon="i-ph-arrow-square-out-bold"
          :to="previewing.site_url"
          target="_blank"
          aria-label="Open website"
          class="ms-auto"
        />
      </header>

      <h1 class="mt-lg text-title tracking-tight">
        {{ previewing?.name }} <span class="text-muted">· Preview</span><Spinner
          :active="busy"
          class="ms-sm align-middle"
        />
      </h1>

      <AddPreviewPosts
        v-if="previewing"
        :posts="previewPosts"
        :source="previewing"
      />
    </div>

    <!-- Pointed at a feed, this commits straight into it, so a refusal has to
         be readable right here. A docked bar, not a screen: px-lg mirrors
         page-inset's sides so the button lines up with the list above. -->
    <div class="bg-default px-lg pt-sm pb-lg *:max-w-reading">
      <p
        v-if="error"
        class="mb-xs text-caption text-error text-inset"
      >
        {{ error }}
      </p>
      <BlockButton
        :label="previewAddLabel"
        icon="i-ph-plus-bold"
        variant="primary"
        :disabled="adding"
        @click="emit('add')"
      />
    </div>
  </div>
</template>
