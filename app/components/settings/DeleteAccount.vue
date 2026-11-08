<script setup lang="ts">
// The confirm in front of deleting the account — the settings twin of
// feed/Confirm.vue: what goes, that it can't be undone, then the action and a
// way out. Account's DangerButton routes here; nothing is deleted until the
// button below is pressed.
const auth = useAuthStore()
const { me } = storeToRefs(auth)

onMounted(() => auth.loadMe())

const pending = ref(false)
const error = ref('')

async function remove() {
  if (pending.value) return
  pending.value = true
  error.value = ''
  try {
    await auth.deleteAccount()
  }
  catch {
    error.value = 'Couldn’t delete your account. Try again.'
    pending.value = false
  }
}
</script>

<template>
  <SettingsPage
    title="Delete account"
    back="/settings/account"
  >
    <div class="flex flex-col gap-xs text-inset">
      <p class="text-body">
        Delete <span class="font-semibold">{{ me?.email }}</span> and everything in it?
      </p>
      <p class="text-caption text-muted">
        Your feeds, saved posts and settings are removed right away, on every device. This can't be undone.
      </p>
    </div>

    <div class="flex flex-col gap-sm">
      <BlockButton
        label="Delete account"
        variant="danger"
        :disabled="pending"
        @click="remove"
      />
      <BlockButton
        label="Cancel"
        @click="navigateTo('/settings/account')"
      />
      <p
        v-if="error"
        class="text-caption text-error text-inset"
        role="alert"
      >
        {{ error }}
      </p>
    </div>
  </SettingsPage>
</template>
