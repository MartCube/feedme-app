<script setup lang="ts">
// Feed-list options action sheet. Unlike the settings/add drawers this is NOT
// route-driven: it's a transient half-height sheet with no navigation of its
// own, so a local open model keeps history clean and never touches the
// nested-route remount trap the layout-mount convention guards against.
const open = defineModel<boolean>('open', { default: false })

const options = [
  { label: 'New folder', icon: 'i-ph-folder-plus-bold' },
  { label: 'Edit feeds', icon: 'i-ph-pencil-simple-bold' },
  { label: 'Reorder feeds', icon: 'i-ph-arrows-down-up-bold' },
]

const { selectedUid, select } = useTapSelection()
</script>

<template>
  <!-- No h-full content override (unlike settings/add): vaul sizes the sheet
       to its content, giving the half-height feel. -->
  <UDrawer
    v-model:open="open"
    :handle="false"
    :ui="{
      content: 'overflow-hidden',
      container: 'gap-0 p-0 overflow-hidden',
      body: 'overflow-hidden',
    }"
  >
    <template #body>
      <div class="touch-none bg-default page-inset">
        <ul class="flex flex-col">
          <li
            v-for="option in options"
            :key="option.label"
          >
            <!-- Placeholder rows — actions get wired in a later pass. -->
            <button
              type="button"
              class="-mx-sm flex w-full items-center gap-sm rounded-2xl px-sm py-sm text-left text-body transition-colors"
              :class="selectedUid === option.label && 'bg-elevated shadow-elevated'"
              @pointerdown="select(option.label)"
            >
              <UIcon
                :name="option.icon"
                class="size-6 transition-colors duration-300 ease-out"
                :class="selectedUid === option.label ? 'text-primary' : 'text-muted'"
              />
              {{ option.label }}
            </button>
          </li>
        </ul>
      </div>
    </template>
  </UDrawer>
</template>
