<script setup lang="ts">
const auth = useAuthStore()
const { me } = storeToRefs(auth)

// A deep load straight into /settings/account has a token but no profile yet.
onMounted(() => auth.loadMe())

// Month + year, not a full date: "Member since" is a tenure, not an event.
const memberSince = computed(() =>
  me.value
    ? new Date(me.value.created_at).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })
    : '',
)

// T8 makes 'google' the only value; until then a token minted by
// manage.py issue_token signs in as 'dev' and should say so.
const provider = computed(() =>
  me.value?.provider === 'google'
    ? { label: 'Google', icon: 'i-ph-google-logo-bold' }
    : { label: 'Development token', icon: 'i-ph-terminal-window-bold' },
)
</script>

<template>
  <SettingsPage title="Account">
    <section>
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted text-inset">
        Signed in with
      </h3>
      <div class="mt-xs flex flex-col gap-px overflow-hidden rounded-2xl">
        <div class="flex items-center gap-sm bg-elevated p-sm">
          <UIcon
            :name="provider.icon"
            class="size-6 text-muted"
          />
          <span class="shrink-0">{{ provider.label }}</span>
          <!-- The email is what gives, not the label: a long address must not
               wrap "Development token" onto two lines. -->
          <span class="ml-auto truncate text-caption text-muted">{{ me?.email }}</span>
        </div>
        <div class="flex items-center justify-between bg-elevated p-sm">
          <span>Member since</span>
          <span class="text-caption text-muted">{{ memberSince }}</span>
        </div>
      </div>
    </section>

    <section>
      <button
        type="button"
        class="w-full rounded-2xl bg-elevated p-sm text-left text-error"
        @click="auth.signOut()"
      >
        Sign out
      </button>
    </section>
  </SettingsPage>
</template>
