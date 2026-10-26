# T14 — Feed preview: implementation plan (DRAFT, for discussion)

Nothing built. The roadmap entry (docs/backend-roadmap.md ~L1761) already fixes most of the
backend contract; this keeps to it and flags only where the code has moved on since.

## 1. Goal

Tapping a discovered candidate in the add wizard shows its 10 newest posts, so the user can
judge "is this feed alive and on-topic" before subscribing. The wizard's `type`/`q` move onto
the `/add` URL so a tapped candidate is addressable and a reload doesn't wipe the flow.

## 2. Open decisions (independent axes)

**A. Where the preview lives in the wizard**
- (a) Inline expand inside the result card
- (b) A new wizard step `preview` between `input` and `destination` — slides in, has Back, has "Select this feed"
- (c) A nested sheet/modal over the search step
- **Pick (b).** Ten rows (title + date + image) don't fit a card on a phone, and expanding fights
  the `touch-none`/vaul drag handling the search step already works around. The wizard is already
  slide panels in `Steps.vue`; a step costs one component + one union member and gets back-nav
  and `direction` for free. (c) adds a second layering context inside a drawer for nothing.

**B. What opens a preview**
- (a) Tapping the card body (today: toggles selection)
- (b) A dedicated "Preview" affordance on the card, beside the existing open-site icon
- **Pick (b).** Multi-select-by-tap is established and the primary path; preview is the "judge it"
  path and sits naturally next to "open site", which exists for the same reason. (a) breaks multi-select.

**C. Preview ↔ selection**
- (a) Preview is look-only; Back returns and nothing is selected
- (b) The preview step has a "Select" toggle writing to `selectedFeeds`, then Back
- **Pick (b).** The user just decided "yes, this one" — making them go back and find the card
  again is friction. Reuses `toggleFeed`, no new state.

**D. Server cache**
- (a) None in v1 (as the roadmap says)
- (b) ~5-min Redis-backed Django cache keyed by `feed_url`
- (c) Read `Post` rows when a `Source` exists
- **Pick (a)** + the wizard-side hold in E. (c) is two code paths; (b) is a five-line add later.
  Watch: Reddit 429s repeated unauthenticated `.rss` fetches, and discovery usually just fetched
  the same URL. If the live test shows it, the answer is (b) with a short TTL — decide after the live test.

**E. Client-side hold of previews**
- (a) Refetch on every entry to the step
- (b) A `previews` map keyed by `feed_url` in the wizard's `useState`, cleared in `reset()`/`selectType()`
- **Pick (b).** Back → forward doesn't refire the network; covers most of what a server cache
  would. One more `useState` in the existing composable, not a new composable.

**F. URL query-param scheme** (the deferred 2026-09-18 decision)
- (a) `type` + `q` only; a tapped candidate stays in state
- (b) `type` + `q` + `preview=<feed_url>`
- (c) Leave the URL alone
- **Pick (b),** via `router.replace` like the post list's `?q=`. Step derives from params: no `type`
  → type step; `type` → input step; `type`+`q` → runs the search on load; `preview` → preview step.
  Picks and the destination step stay in `useState` (as decided 2026-09-18). `preview` is the only
  way the tapped candidate becomes addressable — the stated reason the decision was attached to T14.
  Cost: a deep-loaded `preview=` has only a `feed_url`, no name/icon (see open question in §4).
  If you want this smaller, (a) ships cleanly and `preview` is added later.

**G. `published_at` nullability** (roadmap leaves the split to the builder)
- (a) `entry_to_post(entry, *, clamp_date=True)` — one mapping; preview passes `False` → `None` for dateless entries
- (b) Return the raw date and clamp inside `ingest_source`
- **Pick (a).** One flag, one mapping, ingest behaviour unchanged (pinned by a parity test). (b)
  touches the ingest hot path for no product gain.

## 3. Backend steps

Plain terms: a ninja endpoint is a function with a decorator saying "answer GET /discover/posts,
these are the allowed response shapes"; a `Schema` class describes the JSON (the frontend's
TypeScript types are generated from it). `core/discover.py` holds the logic, `core/api/discover.py`
the HTTP wrapper. We add one function to each.

1. **Rename `_entry_to_post` → `entry_to_post`** in `core/ingest.py`, add `clamp_date` (decision G),
   update its one caller. Moved code, no behaviour change (`feed_metadata` went public the same way in T3).
2. **`core/discover.py`: `preview_feed(feed_url)` + `PREVIEW_LIMIT = 10`.**
   - Fetch through the existing `fetch_page` (SSRF-guarded, 2 MB truncating — private/loopback refused for free).
   - Parse with `feedparser.parse(body, response_headers={'content-location': feed_url})`, as `_from_feed` does.
   - No `parsed.version` → "not a feed"; a version with no entries → `[]`.
   - Map with `entry_to_post(..., clamp_date=False)`, skip `None`s, sort newest first (dateless last), take 10.
   - Reuse the `version` test rather than copying it: a tiny `_parse(body, url)` shared with
     `_from_feed` is justified (it's the load-bearing "is this a feed" rule) — the only helper added.
3. **`core/api/discover.py`: `DiscoverPostSchema` + `GET /discover/posts?feed_url=`.**
   - Fields: `title`, `post_url`, `image`, `summary`, `published_at: datetime | None`.
   - **Roadmap drift:** the roadmap says `image_url`, but T15a made the wire field
     `image: ImageSchema | None` via `resolve_image` → `images.post_image(...)`. Reuse
     `ImageSchema` from `core/api/posts.py` and the same resolver (nothing but `core/images.py` builds image URLs).
   - Operation id `discover_posts`, tag `feeds`, bare list response.
   - Errors: `PageUnavailable`, `requests.RequestException` and not-a-feed → `422 "Couldn't read
     that feed."`; missing `feed_url` → ninja's own 422; `200 []` only for a real empty feed (for a
     preview, empty means "dead", so it must never also mean "unreachable").
4. **No cache, no new timeout** — `fetch_page` already carries `TIMEOUT`/`MAX_BYTES`. No writes, no migration.
5. **Tests** (`backend/tests/`, `tests/feeds.py` bodies, monkeypatching `discover.fetch_page` like the discovery tests):
   - newest 10 of a longer feed, date order, dateless last
   - parity: the mapping equals what `ingest_source` stores from the same body, minus the date (pins the reuse)
   - `RSS_NO_DATE` → `published_at: null`; `RSS_ODD_SCHEMES` skips non-http entries
   - `NOT_A_FEED` / `PageUnavailable` / `RequestException` → 422 + message; version + no entries → `200 []`
   - no bearer → 401; private address refused (one test that the preview goes through the guard)
   - `Source`/`Post` row counts unchanged before/after — "read-only" as a test, not a docstring
   - `image` is a signed proxy dict or null; `tests/test_openapi.py` picks up the operation by itself
6. `pnpm types:api` → regenerate `app/types/api.d.ts`; add
   `export type FeedPreviewPost = Schemas['DiscoverPostSchema']` to `app/assets/types.ts` beside `FeedCandidate`.

## 4. Frontend steps

1. **Wizard state** (`useAddFeedWizard.ts`): `'preview'` in `WizardStep`; `previewing`,
   `previews` (by `feed_url`), `previewLoading`, `previewError`; `openPreview(candidate)`;
   `back()` gains `preview → input`. Same `searchSeq`-style sequence guard against out-of-order
   answers (the file's comments show that race bit once). 422 text via the existing `detailOf`.
   `reset()`/`selectType()` clear it. All logic here — no new composable.
2. **`add/PreviewStep.vue`** (new) — `SearchStep`'s header pattern (Close/Back left, select toggle
   on the far side); body = candidate header (icon, name, URL) then post rows.
   - Loading: 3–4 skeleton rows like the search step
   - Error (422): the server's message in `text-error` + "Try again" (not-a-feed and unreachable deliberately read the same)
   - Empty (`[]`): "This feed has no posts yet." — distinct from error, it means a real, empty feed
   - Loaded: title, relative date ("3 days ago"; "No date" when null, never "just now"), stripped-HTML
     summary line, thumbnail from `image.src`. The newest row's date is the "is it alive" answer —
     make it prominent. Reuse `stripHtml` and the existing card image/date formatting; extract only
     if a second consumer genuinely needs it. Rows open in a new tab, like the open-site icon.
3. **`SearchStep.vue`:** a Preview button per card beside the open-site arrow (`relative z-10`
   above the stretched select button), with an `aria-label`.
4. **`Steps.vue`:** the `v-else-if="step === 'preview'"` panel.
5. **URL params (F)** — the fiddly part: the mobile Drawer reads Nuxt's `useRoute()`, the desktop
   Shell reads `useRouter().currentRoute`.
   - Write `type`/`q`/`preview` with `router.replace` from the wizard actions.
   - On load at `/add?...`, derive the step; run the search for `type`+`q`; open the preview for `preview`.
   - `reset()` clears the params — check against the shell's reset-on-exit-from-`/add` rule.
   - **Open question:** a deep-loaded `preview=` has no candidate object. Rerun the search for `q`
     and match on `feed_url` (restores name/icon, more correct) or show a URL-only header?
     Recommend the rerun, falling back to URL-only when there's no `q`.
   - Check `pages:extend` in `nuxt.config` carries the query (`/add` is synthesized; no `pages/add*` file per `.claude/rules/shell.md`).
6. **Verify:** lint + typecheck + manual review in the running app, mobile and desktop — every
   state, reload and deep-link.

## 5. Files touched

**New:** `app/components/add/PreviewStep.vue`; backend tests (`backend/tests/test_discover_posts.py`
or a section in the existing discovery test file).

**Moved / renamed (no behaviour change):** `core/ingest.py` `_entry_to_post` → `entry_to_post`
(+ `clamp_date`); optionally the shared feed-parse helper out of `_from_feed`.

**Edited:** `backend/core/discover.py`, `backend/core/api/discover.py`, `app/types/api.d.ts`
(generated), `app/assets/types.ts`, `app/composables/useAddFeedWizard.ts`,
`app/components/add/SearchStep.vue`, `app/components/add/Steps.vue`; `add/Drawer.vue` and
`desktop/Shell.vue` only if the composable can't own the URL sync alone. Docs: current-state,
roadmap status line, a decision-log entry for the URL scheme + A–G, and the roadmap's
`image_url` → `image` wording.

## 6. Risks — verify with real messy URLs (`.claude/rules/backend.md`)

- A blog feed, a YouTube `videos.xml`, a subreddit `.rss` — titles, links, dates, images, latency
- A YouTube candidate must preview what polling will show: fetch `youtube.videos_feed()`
  (Shorts left out, 404 → the channel feed) the way `ingest.fetch_feed` does, and skip Shorts
  the way `_entry_to_post` does — not the channel feed raw (added 2026-10-23)
- Reddit 429 on a second hit right after discovery (decides D)
- Huge archive feeds (>2 MB truncated) — newest entries survive, a cut tail doesn't break the parse
- Dateless feeds — "No date" shows, sort stays stable
- Atom vs RSS 2.0 vs RDF; a feed served as `text/html` or with a bad charset
- Redirecting feed URLs (http→https, FeedBurner-style) — the guard re-checks every hop
- An HTML page as `feed_url` → 422, not a crash; `javascript:`/`file:` refused
- Ten raw-HTML summaries — payload size OK; `stripHtml` client-side, no `v-html` on feed content
- A `feed_url` containing `?`/`&` round-trips through `router.replace` and reload
- Shell vs Drawer route reading for the new params
- Fast double-taps and Back during an in-flight preview — the sequence guard holds

## 7. Out of scope

Unifying result shapes across YouTube/Reddit/website or per-type extras (views, upvotes);
server caching unless the live test forces it; `?limit=`/pagination/retention for previews;
Reddit auth (T11c), keyword/catalog search (T11d), storing anything about previewed feeds;
full article text (T10's extraction); preview from anywhere but the wizard; picks or the
destination step in the URL.
