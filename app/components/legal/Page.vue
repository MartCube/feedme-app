<script setup lang="ts">
// The frame Terms and Privacy share: the wordmark, the title, the date it last
// changed, the sections in the slot, and how to reach us. Plain reading pages,
// open signed in or out (middleware/auth.global.ts). The pages using it set
// layout: false, like pages/login.vue.
const props = defineProps<{
  title: string
  updated: string
}>()

useHead({ title: () => props.title })

const contactEmail = useRuntimeConfig().public.contactEmail
</script>

<template>
  <main class="page-inset pb-xl">
    <article class="mx-auto flex max-w-reading flex-col gap-lg">
      <NuxtLink
        to="/"
        class="mt-lg flex items-center gap-xs self-start text-subtitle tracking-tight"
      >
        <Logo class="size-8" />
        <span><span class="text-primary">Feed</span>Me</span>
      </NuxtLink>

      <header class="flex flex-col gap-xs">
        <h1 class="text-title tracking-tight">
          {{ title }}
        </h1>
        <p class="text-caption text-muted">
          Last updated {{ updated }}
        </p>
      </header>

      <div class="flex flex-col gap-lg text-body [&_h2]:text-subtitle [&_p]:text-muted [&_section]:flex [&_section]:flex-col [&_section]:gap-xs [&_ul]:flex [&_ul]:list-disc [&_ul]:flex-col [&_ul]:gap-2xs [&_ul]:pl-md [&_ul]:text-muted">
        <slot />
      </div>

      <p
        v-if="contactEmail"
        class="text-body text-muted"
      >
        Questions? Write to
        <a
          :href="`mailto:${contactEmail}`"
          class="font-semibold text-primary transition-colors hover-darken"
        >{{ contactEmail }}</a>.
      </p>
    </article>
  </main>
</template>
