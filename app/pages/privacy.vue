<script setup lang="ts">
// Plain-language privacy policy for the beta. Kept true to what the backend
// actually stores — change it when that changes (docs/beta-launch.md).
definePageMeta({ layout: false })
</script>

<template>
  <LegalPage
    title="Privacy Policy"
    updated="8 November 2026"
  >
    <p>
      FeedMe is a reader for the websites, YouTube channels and subreddits you follow.
      It is in beta. This page says what we keep about you, why, and how to get rid of it.
    </p>

    <section>
      <h2>What we keep</h2>
      <ul>
        <li>Your email address, and whether you've confirmed it.</li>
        <li>Your password, stored only as a one-way hash we can't read back.</li>
        <li>If you sign in with Google: the account id Google gives us. Nothing else from your Google account.</li>
        <li>What you set up in the app: your feeds and their sources, the posts you save, and your settings.</li>
        <li>For each signed-in device: when it was last used and its browser name, so a session can expire.</li>
      </ul>
    </section>

    <section>
      <h2>What we don't do</h2>
      <ul>
        <li>No ads, and no selling or sharing your data with advertisers.</li>
        <li>No tracking or analytics scripts.</li>
        <li>We don't record which posts you open or read.</li>
      </ul>
    </section>

    <section>
      <h2>Who else is involved</h2>
      <p>
        We use a few services to run FeedMe: a hosting provider for the servers and database, an
        email service to send confirmation and password-reset emails, and Google if you choose to
        sign in with it. They handle your data only to provide that service to us.
      </p>
      <p>
        Images in posts are loaded through our own server, so the sites they come from don't see
        your address. The articles and videos themselves belong to their publishers. Opening one at
        its source, or playing a YouTube video, follows that publisher's own privacy policy.
      </p>
    </section>

    <section>
      <h2>Deleting your data</h2>
      <p>
        Settings → Account → Delete account removes your account and everything listed above right
        away, on every device. Sources nobody else follows stop being fetched. Nothing is kept
        afterwards except what standard server backups hold until they're overwritten.
      </p>
    </section>

    <section>
      <h2>Changes</h2>
      <p>
        If this policy changes in a way that matters, we'll say so in the app before it takes
        effect.
      </p>
    </section>
  </LegalPage>
</template>
