<script setup lang="ts">
// The FeedMe mark: two stacks of three bars. Inline rather than an <img> so the
// left stack follows the theme's accent and the right its body ink — an image
// can't read CSS variables. Decorative: it always sits beside the name.
</script>

<template>
  <svg
    viewBox="0 0 64 64"
    aria-hidden="true"
    class="shrink-0"
  >
    <g class="fill-current text-primary">
      <path d="M30 17L9 11.5a3 3 0 0 0-3.8 2.9v2a3 3 0 0 0 2.2 2.9L30 25z" />
      <path d="M30 29.5L9 24a3 3 0 0 0-3.8 2.9v2a3 3 0 0 0 2.2 2.9L30 37.5z" />
      <path d="M30 42L9 36.5a3 3 0 0 0-3.8 2.9v2a3 3 0 0 0 2.2 2.9L30 50z" />
    </g>
    <g class="fill-current text-default">
      <path d="M34 17L55 11.5a3 3 0 0 1 3.8 2.9v2a3 3 0 0 1-2.2 2.9L34 25z" />
      <path d="M34 29.5L55 24a3 3 0 0 1 3.8 2.9v2a3 3 0 0 1-2.2 2.9L34 37.5z" />
      <path d="M34 42L55 36.5a3 3 0 0 1 3.8 2.9v2a3 3 0 0 1-2.2 2.9L34 50z" />
    </g>
  </svg>
</template>
