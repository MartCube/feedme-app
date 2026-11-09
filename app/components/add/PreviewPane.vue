<script setup lang="ts">
// The desktop feed preview, in the posts pane (DesktopShell swaps it in for the
// posts list while the add wizard has one open). The wizard stays in the right
// pane beside it, its result marked Previewing. Same title row as the posts
// list — pinned on the top-row axis — with the preview's own three actions.
const emit = defineEmits<{ add: [] }>()

const wizard = useAddFeedWizard()
const { previewing, previewPosts, previewAddLabel } = wizard
</script>

<template>
  <div class="flex flex-col">
    <!-- The posts list's title row (FeedPostList), so swapping one for the
         other moves nothing on the top-row axis. -->
    <div class="sticky -top-md z-10 -mx-lg -mt-md box-content flex h-10 items-center gap-sm bg-default px-lg pt-md pb-sm">
      <h1 class="min-w-0 flex-1 truncate text-title tracking-tight">
        {{ previewing?.name }} <span class="text-muted">· Preview</span>
      </h1>
      <div class="flex shrink-0 items-center gap-xs">
        <!-- The one primary icon in the row: the way to act on what you're
             judging. Same as clicking the result's card. -->
        <IconButton
          icon="i-ph-plus-bold"
          :aria-label="previewAddLabel"
          accent
          @click="emit('add')"
        />
        <IconButton
          v-if="previewing?.site_url"
          icon="i-ph-arrow-square-out-bold"
          :to="previewing.site_url"
          target="_blank"
          aria-label="Open website"
        />
        <IconButton
          icon="i-ph-x-bold"
          aria-label="Close preview"
          @click="wizard.closePreview()"
        />
      </div>
    </div>

    <AddPreviewPosts
      v-if="previewing"
      :posts="previewPosts"
      :source="previewing"
    />
  </div>
</template>
