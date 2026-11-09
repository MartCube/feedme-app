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

// The account's way in, not this session's (backend.md § Auth): an account
// with Google linked reads as Google even when this session used a password.
const providers = {
  google: { label: 'Google', icon: 'i-ph-google-logo-bold' },
  email: { label: 'Email and password', icon: 'i-ph-envelope-simple-bold' },
}
const provider = computed(() => providers[me.value?.provider ?? 'email'])

// Nothing waits on confirming (docs/screens-and-flows.md § Login), so this is a
// quiet row, not a banner. "Sent" stays until the panel closes. The API holds
// repeats to one a minute, so a second tap needs no guard here.
const resend = ref<'idle' | 'sending' | 'sent' | 'failed'>('idle')
async function resendConfirmation() {
  resend.value = 'sending'
  try {
    await auth.resendConfirmation()
    resend.value = 'sent'
  }
  catch {
    resend.value = 'failed'
  }
}
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
               wrap "Email and password" onto two lines. -->
          <span class="ml-auto truncate text-caption text-muted">{{ me?.email }}</span>
        </div>
        <div
          v-if="me && !me.email_verified"
          class="flex items-center justify-between gap-sm bg-elevated p-sm"
        >
          <span class="whitespace-nowrap">Email not confirmed</span>
          <span
            v-if="resend === 'sent'"
            class="text-caption text-muted"
          >Sent</span>
          <button
            v-else
            type="button"
            class="text-caption font-semibold text-primary transition-colors hover-darken"
            :disabled="resend === 'sending'"
            @click="resendConfirmation"
          >
            {{ resend === 'failed' ? 'Couldn\u2019t send · Retry' : 'Resend link' }}
          </button>
        </div>
        <div class="flex items-center justify-between bg-elevated p-sm">
          <span>Member since</span>
          <span class="text-caption text-muted">{{ memberSince }}</span>
        </div>
      </div>
    </section>

    <section>
      <BlockButton
        label="Sign out"
        @click="auth.signOut()"
      />
    </section>

    <section>
      <DangerButton
        label="Delete account"
        to="/settings/account/delete"
      />
    </section>
  </SettingsPage>
</template>
