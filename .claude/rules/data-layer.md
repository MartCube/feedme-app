---
paths:
  - "app/stores/**"
  - "app/plugins/**"
  - "app/composables/**"
  - "app/app.vue"
  - "app/assets/types.ts"
---

# Data-layer rules

- **`$api` is the only way to reach the server** (`app/plugins/api.ts`): one `$fetch.create`
  that attaches the bearer and, on 401, clears the session and routes to `/login`. Never call
  bare `$fetch` against the API.
- **Types are generated, never written.** `pnpm types:api` writes `app/types/api.d.ts`
  (committed, ESLint-ignored, hook-guarded); `app/assets/types.ts` is a thin alias layer over
  `components['schemas']`. A missing field means the backend `Schema` needs it — not a hand
  edit.
- **Every call is client-only.** SSR renders the shell; account data loads in `app.vue`'s
  `onMounted`, never in middleware. Each store captures `useNuxtApp()` at setup — actions
  resume past `await` where it has no context to find.
- Stores are `auth`, `feeds`, `settings`. Writes are optimistic-with-rollback except the
  creates (`addFeed`, `addSource`, `relinkSource`), which await the server. **No wrapper
  composables around stores** — use them directly.
- Uids are prefixed and backend-minted: `feed_*`, `source_*`, `post_*`, the fixed `saved_*`
  groups (`app/utils/saved.ts`), plus the literals `all` / `saved`. The resolver reads them in
  that order — one polymorphic `/feeds/{uid}/posts` serves a feed, `all` and `saved`. A
  new public noun is a discussion (`docs/backend.md` § Vocabulary), never a unilateral call.
- Justify every new composable or util, or cut it — say which part is moved code and which is
  new.
