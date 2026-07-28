<script setup lang="ts">
// The post detail: title, time, and body for one post. Rendered by the
// mobile post page and, on desktop, by the detail pane.
const props = defineProps<{ postUid: string }>()

const { posts } = storeToRefs(useFeedsStore())
const post = computed(() => posts.value.find(p => p.uid === props.postUid))
</script>

<template>
  <div class="flex flex-col">
    <template v-if="post">
      <h1 class="mt-lg text-title tracking-tight">
        {{ post.title }}
      </h1>
      <time
        :datetime="post.published_at"
        class="mt-2xs text-caption text-muted"
      >{{ formatDate(post.published_at) }}</time>
      <p class="mt-md text-body">
        {{ post.content }}
      </p>
    </template>
    <p
      v-else
      class="mt-lg text-muted"
    >
      Post not found.
    </p>
  </div>
</template>
