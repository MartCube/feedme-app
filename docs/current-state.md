# Current State

A snapshot of what's actually built vs. what the spec (these docs) describes. The goal is to
make the gap visible so implementation has a clear backlog. Update this as work lands.

_Last reviewed: 2026-10-26._

## Summary

The **design system** and **navigation/drawer UX** are well developed, and the **reader
screens** (feeds list, post list, post page, and a feed's own page) navigate end to end.
**Desktop (≥1024px) v1** now renders those same screens as a three-column shell — sidebar,
posts pane, post pane — composed by the layout from the same routes and store state;
Settings/Add open in the post pane beside the posts list instead of as drawers. **The app
runs on real data** _(2026-09-01)_: a `/login` screen gates every route, and the account's own
feeds, their sources, fetched posts, saved posts and settings all come from the Django API in
`backend/` (Django + django-ninja, Docker Compose) — the mock data files are deleted and nothing
falls back to them. **Writes are real too** _(2026-09-01)_: adding, renaming, switching on and
off, and deleting all go through the API. **The product model was remade** _(2026-10-08)_:
**folders are gone and a feed is a group of sources** — a name, a description and one source or
many. A source can sit in several feeds, with its own name and its own on/off in each; the home
list is flat, and each feed has a page (the info icon beside its title) where its sources are
switched on or off, renamed, relinked and removed. The edit drawer, long-press and home options
sheet are deleted. See Resolved decisions → Feeds are groups of sources. **Sign-in is real**
_(2026-09-03)_: `/login` renders Google's own button and `POST /auth/google` trades its
credential for our bearer token — with the dev-token field deliberately kept beside it for now,
so there are two ways in until the dev path is retired. **Posts now age out** _(2026-09-07)_: a
nightly job prunes unsaved posts past 90 days and, per source, past the newest 500 — saved posts
are exempt at any age — and polling respects the same line, so a source added today arrives
with only the posts inside that window. **Posts are searchable** — `GET /search` _(2026-09-06)_ narrows any feed / saved
list, and the post list (mobile page and desktop posts pane) searches through it from a box on
the list's own title row. What has no endpoint behind it yet says so: the add wizard resolves any
**pasted URL** and searches **YouTube** by channel name, but a keyword under Website or Reddit
still finds nothing, and the home reorder has no UI. **The reader is wired to
`/posts/{uid}/article`** _(2026-09-18)_: the post page renders the extracted article as markup,
falling back to the RSS summary plus **Open source** when extraction can't produce one. See
Resolved decisions → Backend stack & API. **Posts carry real images** _(2026-09-22)_: a signed
`imgproxy` proxy resizes every post image into a 16:9 WebP family, PostCards show it beside the text (a 16:9 family, cropped square there) when
Settings → Appearance → *Post cards* is **Image** (the default — **Compact**, and any post with
no image or a failed load, is date + title alone), and the post page shows the same image as a
hero below the title and its meta row. **The pictures inside an extracted article are proxied too**
_(2026-09-23)_: the reader's `<img src>` is rewritten to the same proxy at read time, fit to
the reading width with no crop, and dropped along with an image that can't be proxied rather
than left hotlinked. **Feed icons are proxied too** _(2026-09-28)_: the add wizard shows one
for every type, with the name's initials when a feed has none. Nothing else consumes them yet.
**The reader got a rework** _(2026-09-28)_: PostCards are now a square thumbnail beside the text
with a meta row (source name, type icon, date) and an excerpt; a **YouTube** post plays in the
post page instead of showing a still; images are sharper (Reddit originals, YouTube `hq720`, no
upscaling on the post page); and on desktop an Appearance setting picks the **reading-pane
split**. The rest of the strategy is specced in [images.md](./images.md) _(2026-09-15)_.
Backend work is sequenced in [backend-roadmap.md](./backend-roadmap.md), which tracks its
own status: **read that file's § Status for what to build next.**

## Built

- **Theme tokens** — 9 `--ui-*` color roles themed in `app/assets/css/themes.css` (five dark
  themes: Ink default, Claude, Dracula, Reddit, Crowd; the old teal/ink/silver ramps are removed), plus the 4-size
  type scale (`text-title/subtitle/body/caption`, plus a brand-only `text-logo` for the wordmark
  — see [design-system.md](./design-system.md) § Type scale) and `shadow-elevated`. The same
  file defines a desktop-only `hover-accent` utility (the row's label goes `primary` on `:hover`,
  nothing else moves) used across list rows, and `hover-lift` (the post card steps to `bg-muted`)
  — see [design-system.md](./design-system.md) § Color roles → Hover state. The
  font family and type scale live in their own `app/assets/css/typography.css` (imported by
  `main.css`, alongside `app/assets/css/article.css` — the sanitised article body's reading
  styles, an `@utility article` with element rules for exactly the allowlisted tags, tokens
  only), and the
  6-step t-shirt spacing scale (`--spacing-2xs…xl` → `p-sm`, `gap-md`, `mt-lg`, …) in
  `app/assets/css/spacing.css`, alongside the `page-inset` utility every page/drawer
  wrapper uses for the screen inset (lg sides/top — md top on desktop — xl bottom).
  See [design-system.md](./design-system.md).
- **Theme switch** — Settings → Appearance picks one of the five themes via the persisted Pinia
  `settings` store (`pinia-plugin-persistedstate`, cookie — now a local cache in front of
  `GET`/`PUT /settings`, see **Data layer** below, which is what still paints the chosen theme
  server-side without a flash); `app.vue` applies `data-theme` on `<html>` via `useHead`.
- **Feed list** _(2026-10-21)_ — the home and sidebar list is always the list treatment (the
  List/Cards setting was removed end to end, `feed_list_style` dropped in migration 0008): rows
  `2xs` apart, selected row = `bg-elevated` + `shadow-elevated` + `primary` name.
- **Scrollbar** _(2026-10-21)_ — one desktop-only scrollbar (the Thin/Comfortable/System setting
  and `data-scrollbar` were removed, `scrollbar_style` dropped in 0008): 6px pill thumb in a 14px
  gutter, `color-mix` of `--ui-bg-muted` toward `--ui-text` (8%, 20% on hover); Firefox uses
  `scrollbar-width: auto`. Rules in `app/assets/css/scrollbars.css` (separate webkit and Firefox
  branches — the two must never target the same element or Chromium 121+ drops the webkit
  rules). Scroll containers use the `scroll-host` utility (`overflow-y-auto` + reserved
  `scrollbar-gutter`). See [design-system.md](./design-system.md) § Scrollbar.
- **Navbar** — `app/components/Navbar.vue` (menu → `/settings`, add → `/add`).
- **IconButton** — `app/components/ui/IconButton.vue` (round soft-fill button, accent press
  flash). A `quiet` variant blends into the page bg at rest and lifts to the normal
  elevated look while the press flash runs (no caller since the home 3-dot options trigger
  was deleted, 2026-10-08). On hover-capable
  pointers the icon itself lights `primary`, the same cue `hover-accent` gives a row's label —
  see [design-system.md](./design-system.md) § Color roles → Hover state.
- **Settings drawer** — `app/components/settings/Drawer.vue` hosts the sheet; the
  `/settings/:panel?` route renders the home component (via `pages:extend`) so the feed list
  stays behind the sheet on mobile, and panels swap as in-drawer components with `panel-slide`
  transitions. Main page (`settings/Home.vue`): in-flow close → title → section list with the
  shared tap-selection flash (row + leading icon accent flash). Subpages (Account / Appearance
  / Keyboard shortcuts, desktop only / About / Report) share `settings/Page.vue`: back + the section's own muted icon + `text-subtitle`
  title as a where-am-I cue (sections defined once in `app/utils/settings-drawer.ts`, exported as
  `settingsSections` and reused by the desktop sidebar). Both `settings/Page.vue` and the route
  map that picks a panel per path read `useRouter().currentRoute` rather than Nuxt's `useRoute()`
  so they stay correct when rendered inside the desktop content overlay (see Desktop shell v1,
  below). Appearance and Account are functional (theme/post-card switches; real
  profile + Sign out — see **Auth & login** below); About is static info (hardcoded version string) and
  Report is still a mock panel.
- **Add-feed wizard** — `app/components/add/Drawer.vue` hosts the sheet, like the settings
  drawer. The `/add` URL renders the home component (via the `pages:extend` hook) so the feed
  list stays behind the sheet on mobile; the navbar **+** links straight to `/add` (no dropdown),
  and close routes back to `/`. The four-phase slide switch itself lives in
  `app/components/add/Steps.vue` (`AddSteps`, emits `close`/`done` — the host decides what those
  mean, which is what lets the desktop content overlay reuse it), state in
  `useAddFeedWizard()`: **pick type** (`add/TypeStep.vue`, cards with an accent caret tap flash) →
  **paste/search** with a Paste chip, a loading skeleton (kept for the real search; nothing is
  in flight today), and results as **multi-select cards**
  (whole card toggles a trailing page-bg circle "well" that gains an accent checkmark when
  picked; a header forward button at IconButton size — disabled until ≥1 picked, accent when
  enabled — advances) (`add/SearchStep.vue`) → **choose destination** — a quiet "Adding"
  caption + plain titles list of the picked sources above an "Add to" caption + destination
  cards: **New feed** first (always there, the common case for a first source), then one card
  per existing feed with its source count, so only tappable things read as cards; **tapping a
  feed commits all picked sources there** (many sources → one destination) and closes
  (`add/DestinationStep.vue`) → or **New feed** → a name input, prefilled with the first picked
  source's name, whose submit arrow creates the feed and closes (`add/NewFeedStep.vue`, the old
  `FolderStep.vue` renamed and re-pointed). With several picks the feed is created with the
  first (`POST /feeds` carrying its `feed_url`, so one that isn't a feed leaves no empty feed
  behind) and the rest are added to it one at a time; a refusal stops the rest, and the ones
  already in stay in. Phases slide with the `panel-slide` classes in
  `transitions.css`. Headers follow the settings drawer's language: step 1 has an in-flow close
  above the title; steps 2–4 have a md caret back + `text-subtitle` title (no close). The search
  input is enlarged for mobile (taller padding, `text-body`, `rounded-2xl`).
  **Pointed at a feed** _(2026-10-08)_: the feed page's *Add source* sets the wizard's `target`
  to that feed (`useAddFeedWizard().target`, cleared by `reset()`) before opening `/add`; the
  wizard then skips the destination step and commits straight from the search step.
  Committing calls `useFeedsStore().addFeed()` for a new feed or `addSource()` per picked source
  for an existing one, which `POST` to `/feeds` and `/feeds/{uid}/sources` and await the
  server's whole feed (uids are minted server-side). Adding is the one step that can be
  **refused**, and the refusal surfaces in every place that commits: `add/DestinationStep.vue`,
  `add/NewFeedStep.vue` and — for the targeted add — `add/SearchStep.vue`. It's the API's
  `detail` verbatim ("That URL isn't a feed.", "That source is already in this feed."), sitting
  **above** the destination list (the panel is `touch-none`, so anything below a long feed list
  is out of reach on mobile), with the destination cards disabled while the request is in
  flight; the sheet **only closes on success**. The search step calls
  **`GET /discover`** _(T11a, 2026-09-06)_: a pasted URL resolves whether or not it is the feed
  URL — a blog homepage or a post page, a YouTube channel URL or `@handle`, a subreddit URL or a
  bare name. A result already in one of the user's feeds **stays pickable** _(changed
  2026-10-08; it used to be dimmed and locked as "Following")_ with an **"In your feeds ·"**
  caption in front of its feed URL, and each row is captioned with that **feed URL**, since one
  page can declare several feeds and that is what tells them apart. _(2026-10-08)_ A YouTube
  search hit shows its **subscriber count** instead of the URL, and every result carries an
  open-in-new-tab link to its channel or site (`site_url`). A **keyword under the YouTube card** searches
  YouTube by channel name _(T11b, 2026-09-11)_: up to five channels, each row leading with the
  channel's avatar (through the image proxy since T15b, _2026-09-28_ — before that a hotlink
  with `referrerpolicy="no-referrer"`, since Google's image CDN 429s a hotlink carrying a
  foreign referrer), and the same `videos.xml` feed URL
  a pasted channel resolves to, so adding it
  is the same call either way. YouTube refusing to answer (quota spent, key rejected) is
  a **503** the step shows as an error — not "nothing found", which would be a lie. A keyword
  under Website or Reddit still says "Nothing found. Try pasting a link." (T11c, T11d).
- **Feed page** _(2026-10-08)_ — replaces the whole edit drawer. `app/components/feed/Info.vue`
  (`FeedInfo`) is a feed's own page: a back caret (hidden on desktop, where the list is already
  beside it, but keeping its space), a pencil to edit, the name in `text-title`, the
  description, then "Sources n/m" (on out of total) and one row per source — the name as a
  link to the source's page (dimmed by opacity alone when off, so the row's inherited accent
  still reaches it) and a `ui/Toggle.vue` **outside** the link (interactive in interactive is
  invalid) that flips it on or off **immediately** through `feedsStore.updateSource`, with no
  Save. Below the list a dashed full-width ghost row, **Add source**, resets the add wizard,
  sets its `target` to this feed and navigates to `/add`; an empty feed says "No sources yet."
  and keeps the row. `feed/InfoPanels.vue` (`FeedInfoPanels`) is the one switch
  over the views, shared by both hosts (the mobile page and the desktop post pane), so they look
  and behave alike; `utils/feed-info.ts` (`infoView`, `infoBack`, `restOf`) names each view from
  the path's tail and where Back from it goes. The views are routes under `/feed/:uid/info`,
  all rendered by one catch-all page, `pages/feed/[uid]/info/[...rest].vue` (which captures the
  uid and tail once, so the leaving page keeps its content through the slide, and wires
  `useSwipeBack` to `infoBack`):

  | Path | View |
  | --- | --- |
  | `/feed/:uid/info` | the feed page |
  | `…/info/edit` | `feed/InfoEdit.vue` — Name and Description inputs, a **Save** `ui/PillButton.vue` (live once a draft differs and the name is non-empty; Save returns to the feed page), and a `ui/DangerButton.vue` **Delete feed** |
  | `…/info/delete` | `feed/Confirm.vue` — "Its sources leave your list unless another feed has them. Saved posts stay." Confirming deletes and goes home |
  | `…/info/source/:sourceUid` | `feed/SourceEdit.vue` — a **Name** input with the source's own title as its placeholder (blank = that title), a **Link** input, a **Save** pill, and a `DangerButton` **Remove from this feed** |
  | `…/info/source/:sourceUid/remove` | `feed/Confirm.vue` — "It stays in your other feeds. Saved posts stay." Confirming removes and returns to the feed page |

  Back is the parent view (remove → source → feed page → post list; delete → edit → feed page).
  Saving a **name** is optimistic; saving a **link** awaits `relinkSource`, since the new URL is
  fetched and may not be a feed — the API's reason shows under the field, nothing changes, and
  the form stays up; success goes to the feed page (a new link is a different source with a
  different uid in the path). A feed or source that no longer exists — a stale link, a delete on
  another device — sends the reader to the feed page, or home if the feed is gone, held until
  `/home` has answered so a deep link doesn't bounce mid-load.
  `ui/DangerButton.vue` is still the app's one destructive affordance — an elevated full-width
  card, no icon, muted label — that **arms** on tap (`animate-pulse` + `text-error` for 250ms,
  deliberately under the 0.35s panel-slide since the red flip is instant) and then routes to a
  confirm view; it never mutates the store itself. `feed/Confirm.vue` is the old
  `edit/ConfirmPanel.vue` moved: purely presentational — props
  `action`/`verb`/`subject`/optional `context`/`note`/`backTo`, emits `confirm`; its
  Confirm/Cancel are `ui/BlockButton.vue`. Row content is inset `sm` as real padding on the row
  rather than a `text-inset` margin on the list, so row text lines up with the heading.
  **Mobile:** an info icon beside the post list's title (`feed/PostList.vue`) links to `/feed/:uid/info`; the
  middleware's depth rule makes that a push with the page slide, and `useSwipeBack` pops it.
  Home and Saved have no icon. **Desktop:** the post pane renders `FeedInfoPanels` (body
  capped at `max-w-reading`) whenever no post is open and the uid is a `feed_*` — replacing
  the "Select a post" placeholder, which Home and Saved keep — and the icon links to `/feed/:uid`,
  which closes the post. The store mirrors the view as `readerInfo` (the path tail, or null)
  beside `readerFeedUid`/`readerPostUid`, so it survives Settings or Add opening over the
  reader. **Deleted with it:** `edit/Drawer.vue`, `Panels.vue`, `FolderPanel.vue`,
  `FeedPanel.vue`, `home/OptionsDrawer.vue`, `useLongPress`, `utils/edit-drawer.ts`, the
  `/edit/*` routes in `nuxt.config.ts`, and the desktop overlay's edit branch.
- **Layouts** — `app/layouts/default.vue` is the single layout and the mobile/desktop branch
  point: `useIsDesktop()` (`app/composables/useIsDesktop.ts` — VueUse `useMediaQuery` at the
  `lg` 1024px tier, gated behind `useMounted` so SSR and the hydration render always emit the
  mobile tree, flipping only after mount on wide clients) chooses between the unchanged mobile
  tree (`lg:hidden`-masked for a wide first paint, hosting the two drawers — Settings and Add) and
  `DesktopShell`. `isDesktopNow()` is the synchronous twin for imperative guards.
- **Desktop shell v1** (`app/components/desktop/`) — ≥1024px renders three columns composed
  straight from the route and the `feeds` store, not a nested-route tree: `Sidebar.vue` (18rem)
  — the shared `HomeFeedList` in `grouped` mode (wordmark, Home, Saved, a **New Feed** row
  (→ `/add`) slotted after Saved, then the feeds folded under a **Feeds** header — see Feeds
  list v1, below), then a **Settings** group listing the settings sections directly (see
  Sidebar groups _(2026-10-21)_); a
  posts pane (`FeedPostList`, 50% by default — the Appearance split); and a post pane (the rest, body capped at 56rem, a `FeedPostActions` bar — Copy link, Open source and Save — right-aligned above
  `FeedPostView` once a post is loaded; with no post open, the **feed page** — see Feed page,
  above — or, on Home and Saved, a dimmed "Select a post" placeholder — **no auto-select**).
  `Shell.vue` reads `useRouter().currentRoute` rather than Nuxt's `useRoute()` (Nuxt's route
  object only resyncs when a `NuxtPage` resolves, and the shell renders none), syncing the
  feeds store's `readerFeedUid`/`readerPostUid`/`readerInfo`/`readerQuery`/`readerPath` on reader routes only
  — they stay frozen while a content route is open (which is what keeps a search alive across a
  trip into Settings).
  **The three columns share a pinned top-row axis** _(2026-09-24)_: the sidebar wordmark, the
  posts pane's title/search row, and the post pane's actions row all sit in one 40px row (`lg:h-10`) at
  the top inset — `md` from the window edge on desktop _(2026-10-23; was 48px at `lg`)_ — and all three are `sticky` at `-top-md` (not `top-0` — Chrome measures a sticky
  offset from the scroll container's *padding* edge, not its border box) so each stays reachable
  while its own column scrolls under it. Each pinned row folds its column's `page-inset` into an
  opaque strip in the column's own surface — `bg-sunken` for the sidebar, `bg-default` for the
  two reading panes — rather than a divider. Mobile is unchanged: the post list's title still
  clears the navbar with `mt-lg`, and mobile navbars aren't pinned.
  Settings and Add open **inside the post pane** _(2026-10-13; was a `ContentOverlay.vue` laid
  over both reading panes, now deleted)_: the posts list stays visible and interactive beside
  them, along with the sidebar, and the reader underneath stays mounted but `inert` (open post,
  search and pane scroll all survive a round-trip). **Nothing on desktop slides** — the pane
  appears and disappears like a page replacing a page, and the `.content-slide-*` classes are
  gone from `transitions.css` (see Resolved decisions → Desktop motion). It is the phone's
  single-pane stack minus the slide: a settings section or the next add step **replaces** the
  pane, and the panels' own back buttons walk it, with the settings section list at `/settings`
  and the add wizard at `/add`, both held to `--container-reading`. With no feeds, the empty
  state takes the posts pane's place while they are open. The area reuses the exact mobile panel
  components (`app/utils/settings-panels.ts`'s route map, `AddSteps` with `slide` false) and
  resets the add wizard on any exit from `/add` (the shell watches the route). The two drawer
  hosts guard their `onMounted` open-on-deep-load with `isDesktopNow()` so a desktop deep-load
  of `/settings/*` or `/add` never flashes a bottom sheet.
  Layout tokens live in `app/assets/css/layout.css` (`--container-sidebar/postlist/reading/post`,
  a `@theme static` block in its own namespace so it doesn't collide with the six-name
  `--spacing-*` rule) — there is no whole-shell width cap. **v1 is deliberately unpolished:**
  keyboard focus rings still suppressed — queued for a later design/polish pass.
- **Empty / unreachable state** — `app/components/home/EmptyState.vue` carries two states in one
  layout: the first-run nudge ("Nothing here yet" + an explainer + a primary "Add your first
  feed" action → `/add`), driven by the `feeds` store's `hasFeeds` computed (feeds non-empty),
  and — when `GET /home` failed — "Can't reach the server" + a **Try again** action
  that retries the load. Neither renders until the store is `loaded` (or has failed), so the
  first paint can't flash "Nothing here yet" while the request is in flight. Shown on the mobile
  home page in place of the list, and on desktop in place of both reading panes (the sidebar
  keeps working, so Add feed stays reachable). New spec surface — nothing was specced for the
  zero-feeds state before.
- **API client & types** — `runtimeConfig.public.apiBase` (default
  `http://localhost:8000/api/v1`, override `NUXT_PUBLIC_API_BASE`) and `app/plugins/api.ts`,
  a `$fetch.create` instance (`$api`) that is the one way the app talks to the server: it
  attaches `Authorization: Bearer` on request and, on a 401, clears the session and redirects to
  `/login` (inside `nuxtApp.runWithContext`, since an ofetch hook runs outside the Nuxt
  context). Types are **generated from the API**: `pnpm types:api` runs `openapi-typescript`
  against `/api/v1/openapi.json` into `app/types/api.d.ts` (committed, so typecheck doesn't need
  Docker; ESLint-ignored). `app/assets/types.ts` survives as a thin alias layer over
  `components['schemas']` — `Feed` (a group of sources), `Source` (one source as it sits in a
  feed — `FeedSourceSchema`), `Post`, `FeedType`, plus `Home`/`PostPage`/
  `Settings`/`Me`/`SavedGroupName` — so component imports are unchanged and a renamed backend
  field breaks typecheck instead of silently rendering blank. `FeedCandidate` is generated too as of
  T11a — `DiscoverResultSchema`, a source's name, type, site, feed URL and icon plus
  `already_subscribed` (now "in one of your feeds").
- **Auth & login** — `app/pages/login.vue` (brand, one line, then **two controls**: Google's
  rendered sign-in button and, below it, the dev-token field — both ship, see Not started →
  Sign-in (rest); `definePageMeta({ layout: false })` is load-bearing, since the default
  layout renders `DesktopShell` instead of the page above 1024px). The Google button is loaded
  with VueUse `useScriptTag` and rendered by Google Identity Services into a wrapper that
  **clips its iframe's 10px bleed**; its chrome is Google's (hence `theme: 'outline'` — a clipped
  dark button inverts the app's elevation direction), and the column is capped by a new
  `--container-signin` (29rem) because Google caps its button at 400px. A missing
  `runtimeConfig.public.googleClientId` renders no button at all and leaves the dev field as the
  way in. `app/stores/auth.ts` holds the token (cookie-persisted, `pick: ['token']` only) and the
  `/me` profile; `signInWithToken()` proves a token against `/me` before keeping it, so a bad
  token fails on the login screen instead of as a redirect loop, and `signInWithGoogle()` only
  adds the step before it — `POST /auth/google`, then hand the returned token to the same path.
  Errors are **one message per control**, and `app/plugins/api.ts`'s global 401 handler skips
  `/auth/google`, so a refused credential leaves a live session untouched.
  `app/middleware/auth.global.ts` is a **pure guard** — everything except
  `/login` needs a token, and it does no fetching (see Resolved decisions → Backend stack & API
  → T6). Sign out (Settings → Account) revokes the token server-side via `POST /auth/logout`,
  clears both stores, and returns to `/login`; Account's "Signed in with" row reads `google` for
  a linked account even in a dev-token session, because `provider` describes the account.
- **Data layer** — the `feeds` store loads `GET /home` once (in-flight-guarded; a failure is
  swallowed rather than raised, so it can never surface as Nuxt's error page, and retries from
  the home screen's **Try again** or the next app boot) into `feeds` — each a group with its
  sources — behind a `loaded` gate and an `unreachable` flag. The feeds
  arrive in display order (the server sorts by its one order column) and the response carries no
  order of its own; reordering waits on its UI — see Not started → Home reorder.
  `app/composables/usePostList.ts` cursor-pages `GET /feeds/{uid}/posts` (limit 10) behind a
  sentinel + VueUse `useIntersectionObserver` rooted on the viewport, so the same composable
  serves the mobile page scroll and the desktop pane; given a query it pages `GET /search`
  instead, with the uid as `scope` — same page shape, same cursor, same failure rules, so
  searching is a different URL and nothing else, and a changed query resets the list exactly as
  a changed uid does. `app/composables/usePost.ts` owns one post
  plus its save toggle. The `settings` store loads `GET /settings` and `PUT`s on change (a full
  replace of all three synced fields). Both loads run from
  `app.vue`'s `onMounted` (and again on sign-in), never from middleware — see Resolved decisions.
  **Writes** _(2026-09-01, reshaped 2026-10-08)_: every `feeds`-store action calls the API.
  `updateFeed`, `deleteFeed`, `updateSource` (rename and on/off) and `removeSource` are
  **optimistic with rollback** — the local array is replaced first and a shared `commit()` helper
  restores the previous one if the request fails, and on success swaps in the server's copy of
  the **whole feed** (every feed write answers with one, so the store replaces a row — `put()` —
  instead of patching fields, and a rename's fallback title or a new link lands exactly).
  `addFeed`, `addSource` and `relinkSource` **await** instead and let their error escape to the
  add wizard or the source form, because the backend mints every uid and fetches a new URL to
  find out whether it is a feed at all. The store also keeps `postsRevision`, a counter bumped
  when a write that changes which posts a feed holds has **landed** — a source switched on or
  off, added, relinked or removed, a feed created or deleted — and never on the optimistic
  flip, since a list refetched before the server has the write reads the old posts.
  `usePostList(uid, q, contents)` takes the caller's `contents` string as a third argument
  (only compared, never sent): a change resets the list exactly as a changed uid or query does,
  and `feed/PostList.vue` passes the revision for every uid except the saved lists.
- **Feeds list v1** — `app/components/home/FeedList.vue` (`HomeFeedList`) renders the home list
  from the `feeds` store's `/home` load — used by the mobile home page (`app/pages/index.vue`)
  and, on desktop, the sidebar (an `activeUid` prop drives the desktop persistent-selection
  highlight). It leads with the **FeedMe logo mark** (`ui/Logo.vue`, `size-8`) and wordmark (`text-logo`, Feed in `text-primary`,
  ME in body ink; mark and wordmark share one link; see
  [design-system.md](./design-system.md) § Type scale; the mark itself links to `/feed/all`, the
  link sized to the text so the row's dead space isn't a target; on desktop the row is pinned to
  the top of the sidebar, on the top-row axis it shares with the posts pane's title row and the
  post pane's actions — see Desktop shell v1), then **Home** as an ordinary list row —
  same height and surface as every other row, just `Home` (the `all` feed's display title; was
  `All feeds` until 2026-10-21) — linking
  to `/feed/all` (the merged read of every source that's on in some feed), then a pinned
  **Saved** row (links to `/feed/saved`; the total count beside it is gone from the list as of
  2026-10-21 — the code no longer renders it, while screens-and-flows.md still specs it), then one row per
  feed: the name, and a count of its sources beside it unless it has exactly one (so a
  multi-source or empty feed shows its count), linking to `/feed/[uid]`. **The list is flat**
  _(2026-10-08)_: no expand chevrons, no trailing ⋯ buttons, no long-press, and the options
  sheet that Home's 3-dot opened is deleted — everything done to a feed lives on its feed page.
  Names only — no type icons. Every row carries the shared desktop `hover-accent` (label to
  `primary` on hover), and a selected row — the tap flash on mobile, the persistent desktop
  selection — lights its **name** `primary` on top of the elevated surface. Rows sit `2xs` apart so a selected row's
  rounded surface doesn't fuse with its neighbour. See [design-system.md](./design-system.md)
  § Color roles → Hover state.
- **Post list v1** — `app/components/feed/PostList.vue` (`FeedPostList`, `uid` + `q` +
  `activePostUid` props) lists PostCards with the resolved feed name as title — used by
  the mobile page (`app/pages/feed/[uid]/index.vue`) and, on desktop, the shell's posts
  pane. (This is the screen docs called "Feed page" until 2026-10-08; "feed page" now means a
  feed's own page, above.) An **info icon** after the title links to the feed page —
  `/feed/:uid/info` on a phone, `/feed/:uid` on desktop, where the page already fills the post
  pane and the link just closes the open post; the title is plain text, and All feeds has no
  icon. Posts come from
  `usePostList(uid, q, contents)` — the uid resolves **server-side** in the
  frontend's own order (`all` → `saved` → `saved_*` → `feed_*`), so the component
  filters nothing and just renders what pages in; a uid change resets the list rather than
  appending, and so does the store's `postsRevision` changing (see Data layer), so switching a
  source off on the feed page is reflected the moment the write has landed. The list says "No posts here yet" when a stream is genuinely empty and "Couldn't
  load posts." when a page request failed (paging stops rather than retrying into a refusing
  server).
  **Search** lives on the title row: a magnifying-glass `IconButton` — the standard `md`
  elevated style, matching the post actions, not the smaller quiet one it used to be — swaps
  the title for a `SearchInput` (placeholder "Search *{title}*", so the list being searched is
  named without a noun that would be wrong for a feed or Saved; no submit arrow — the field is
  live) and back to an X that closes it. Typing is debounced 300ms into `?q=` on the route via
  `router.replace` (never `push` — Back must leave the page, not walk the term backwards), and
  the list pages
  `GET /search` scoped to the same uid, ordered by recency; an empty result says *No posts match
  "…"* with the term. The host owns the query the way it owns the uid: the mobile page reads `route.query.q`
  (frozen the moment the page starts leaving, so results don't blank mid-slide), the desktop
  shell the store's `readerQuery` mirror. A result's link carries the query, so Back from a post
  lands on the results, and a deep link with `?q=` opens the box filled. Closing is immediate; a
  uid change clears it. The mobile navbar's magnifying glass is gone — this row is the entry on
  both viewports, since the desktop pane has no navbar; on desktop the row is pinned to the top
  of the pane, on the same top-row axis as the sidebar wordmark and the post actions (see
  Desktop shell v1).
  `feed/[uid].vue` stays a `<NuxtPage/>` passthrough on
  mobile; on desktop the shell bypasses it (and every route's `<NuxtPage/>`) entirely, composing
  the posts/post panes itself from the feeds store.
- **Post page v1** — `app/components/feed/PostView.vue` (`FeedPostView`) renders, in order, the
  title, the **meta row** (`feed/PostMeta.vue`, shared with the PostCard — see PostCard v2), the
  image or video, and the post body _(reordered 2026-10-08: the image used to come before the
  title)_; it is **presentational** — the host that owns the uid (the mobile post page, or
  the desktop shell for its post pane) fetches through `usePost(uid)` and passes the post and
  article down, because the host also needs the title and the save state. **The reader is wired
  to `/posts/{uid}/article`** _(2026-09-18)_: `usePost` fires it concurrently with
  `GET /posts/{uid}` and exposes `article` (the html, or `null`) and `articleState` (`loading` /
  `ok` / `unavailable` — a thrown request is treated the same as the endpoint saying so, since
  the screen does the same thing either way). The body follows that state: a `USkeleton` while
  loading; the article as markup via `v-html` when `ok` — the one field the app renders as HTML,
  safe because the backend sanitises it server-side against its own allowlist
  (`core/extract.py`); and, when `unavailable`, the stripped RSS `summary` as before plus an
  inline "Read the full post" link to `post_url`. Links inside the article open in a new tab
  through one delegated click handler (the sanitiser keeps `<a href>` but no `target`; this is
  also the hook a future Capacitor Browser plugin replaces). Reading styles live in
  `app/assets/css/article.css` — an `@utility article`, element rules for exactly the allowlisted
  tags, tokens only — imported by `main.css` beside `typography.css`. **Copy link, Open source
  and Save are one component**: `app/components/feed/PostActions.vue` (`FeedPostActions`, props
  `post` + `saved`, emits `toggle-save`) renders three `IconButton`s — **Copy link** _(2026-09-24)_
  (copies `post.post_url` — the source's own URL, not a FeedMe one, since opening a FeedMe link
  needs an account — via VueUse `useClipboard({ legacy: true })`, whose `legacy` `execCommand`
  fallback covers plain-http LAN dev where `navigator.clipboard` is missing; the icon swaps to a
  checkmark for 1.5s), **Open source** (`post_url`, new tab), and **Save**. The mobile post page's
  navbar uses it; **the desktop post pane now has one too** — right-aligned within `max-w-post`,
  and, as of the same date, pinned to the top of the pane on the shared top-row axis (see Desktop
  shell v1) rather than sitting above the scrolling content, height still reserved so the title
  doesn't drop when the post arrives — so **saving is no longer mobile-only**. The mobile
  navbar's bookmark toggle underneath is unchanged: `PUT`/`DELETE /posts/{uid}/save` into
  **Bookmarks** (Save is a toggle, not a group chooser), reflected in the icon and
  `aria-pressed`.
- **Polish pass** _(2026-10-13)_ — frontend. **Icon buttons**: the tooltip opens above, icons
  rest `text-muted` and light `primary` on hover and press. **Inputs** show one `primary` focus
  line. **Loading**: a spinner beside the sidebar/home wordmark (`home/FeedList.vue`) driven by
  an in-flight counter on the `$api` plugin (`$apiPending`), debounced 150ms; the mobile feed and
  post pages have none yet, and a custom spinner is a backlog item. **Post actions side**
  _(removed 2026-10-23: the layout is fixed to actions left, Back right, and `actionSide` is gone
  from the settings store)_. The actions stay mounted while the
  next post loads (inert until it arrives, hidden if it failed), so they don't blink between
  posts. **Feed info**: an info `IconButton` beside search in the posts title row replaces the
  glyph on the title; the feed page has separate Delete and Edit buttons, Delete moved out of
  `InfoEdit`, and back from the delete confirm returns to the feed page. **Add wizard**: Enter
  submits the new-feed name; on success the app navigates to the landed feed and selects it
  (mobile closes the sheet first). **Desktop**: Settings and Add open in the post pane (see
  Desktop shell v1). `PostView`'s root is `isolate` so `PostMeta`'s `z-10` source link no longer
  paints over the desktop sticky strip; `pages/feed/[uid].vue` wraps `<NuxtPage>` in a plain
  `div` (fixes a Vue transition warning from a non-element root). New `hover-darken` utility for
  links resting in `primary` (restated in `article.css`) — see
  [design-system.md](./design-system.md). **Post images**: `PostImage` fixes its box at the
  aspect from first paint with `animate-pulse` until load, and under `noUpscale` a smaller
  image sits centred at its own size — **this delivers roadmap T15f**. The feed search is `h-12`
  to match `IconButton` (`h-10` on desktop).
- **Desktop density and logo pass** _(2026-10-23)_ — frontend. **Logo**: `ui/Logo.vue` mark
  beside the wordmark, `text-logo` 2rem → 1.625rem, `public/favicon.svg` replaces the stock
  favicon. **Top-row axis**: `page-inset` takes `md` top on desktop; sidebar wordmark, posts-pane
  title row and post-action strip are 40px rows pinned at `-top-md`; `scroll-under-strip` is
  `md + h-10 + sm + xs`. **Sizes on desktop**: `IconButton` `md` is `size-12` (`lg:size-10`, icon
  `size-6` / `lg:size-5`), the Add Continue button matches, `PillButton` `lg:h-10`, `SearchInput`
  `h-12` / `lg:h-10`. **Tooltip**: bare 11px muted text, desktop only (see design-system.md).
  **Density**: sidebar rows `py-xs`; post cards `lg:py-xs`, image cards `lg:pr-xs` with the image
  `lg:rounded-lg` (an even `xs` frame, concentric corners); card image `md:size-40` /
  `xl:size-44` (was `lg:size-44` / `xl:size-48`); post view title `lg:mt-xs`. **Removed**: the
  Appearance → *Post actions* setting.
- **Sidebar groups** _(2026-10-21)_ — frontend. The desktop sidebar is three groups: pinned
  rows (Home, Saved, **New Feed**), a foldable **Feeds** group, and a foldable **Settings**
  group that lists the settings sections directly (one click opens a section; the post pane's
  own section list is no longer reached on desktop, and a section's top button is **Close**
  rather than Back). Folds use `UCollapsible` with the new `ui/GroupToggle.vue` header
  (caption-styled, hairline, caret) and a 200ms fade/slide (`fold-rows` in `motion.css`). Three
  new **local-only** settings (cookie-persisted, not in the account payload, like the other local-only settings):
  `sidebarIcons` (`shown` default | `hidden`; desktop only; Appearance → *Sidebar icons*) and
  `feedsGroupOpen` / `settingsGroupOpen`. All persisted-store cookies (these and the auth
  token) carry a 1-year `maxAge` _(2026-10-23)_; before, they were session cookies, so closing the
  browser signed you out and reset these. The `all` feed's display title is now **Home**
  (was "All feeds"). **Home and Saved have no feed page**: `FeedInfoPanels`/the info icon apply
  to `feed_*` uids only, and `feed/Info.vue` no longer lists Saved's groups. The feed page's
  header puts actions left and Back right.
  Add wizard steps gain a Close button beside Back on desktop, and Add/Settings/feed-page
  panels hold their content to `max-w-reading` inside a full-width scroll (scrollbar at the
  pane edge). Continue in the wizard blinks `primary` once when first enabled.
- **More themes** _(2026-10-23)_ — Dracula, Reddit and Crowd join Ink and Claude (settings
  `theme` enum widened, migration 0009). Crowd deviates on purpose: sidebar a step above the
  page, cards on the sidebar surface, a scoped hover-surface exception — see
  [design-system.md](./design-system.md) § Themes. Persisted cookies now last a year.
- **Desktop keyboard shortcuts** _(2026-10-21)_ — frontend, ≥lg only, on Nuxt UI's
  `defineShortcuts` (no new composable; each binding lives in the component owning its state).
  Esc (`DesktopShell`, works from focused fields; ignored during IME composition) closes the top
  layer one per press: Settings/Add → frozen reading position; feed sub-view → its `infoBack`; open
  post → feed page (keeps `?q=`); bare feed page → the search, if open (after Enter blurred the
  box), else nothing. The posts search keeps its own Esc and stops propagation. In
  `FeedPostList`: `/` opens and focuses search (`SearchInput` exposes `focus()`); ↓/↑ step the
  open post (first open = history push, later = replace; inactive in inputs and while
  Settings/Add is open) _(refined 2026-10-26)_: each arrow is bound only while there is a post to
  step to, so at the list ends it stays the pane's scroll key; a held arrow steps once; an open
  post missing from the list (deep link, filtered by search) has no neighbours, so the arrows
  don't jump to the first post; Enter in the live search blurs so arrows step results. Arrows chosen over
  j/k. The pane follows the open post (`scrollIntoView` nearest, smooth, auto under reduced
  motion) via the `scroll-under-strip` utility, watching the open uid only. New Settings section
  **Keyboard shortcuts** (`/settings/shortcuts`, after Appearance): `settingsSections` entries can
  carry `desktop: true`, which the settings Home list filters out on a phone; the panel
  (`settings/Shortcuts.vue`) is a static list grouped Reading / Search / Anywhere with `UKbd`
  caps restyled `bg-muted`, no ring. Adding a shortcut = its binding + one row there. Not built:
  `?` cheat-sheet overlay, key hints in tooltips.
- **YouTube polled videos-only** _(2026-10-26)_ — backend. A YouTube source is polled through the
  channel's videos-only feed (`videos.xml?playlist_id=UULF<id after UC>`, `core/youtube.videos_feed`
  via ingest's `fetch_feed`), which leaves out Shorts and live streams; the stored channel
  `feed_url` stays the source's identity, so no migration. On a 404 (a channel with no regular
  uploads) it falls back to the channel feed, and `_entry_to_post` skips Shorts (`/shorts/` links).
  The playlist is titled "Videos", so name and `site_url` come from the feed's author. The T14
  feed preview must read the same videos-only feed for YouTube (see
  [backend-roadmap.md](./backend-roadmap.md) § T14).
- **Article extraction cleanup** _(2026-10-26)_ — backend, `core/extract.py`. Before trafilatura,
  `_drop_boilerplate` removes containers and paragraphs whose class / id / `data-testid` /
  `aria-label` carries related, recommend, newsletter, subscribe, share, promo, affiliate or
  comment (or the pairs more-on, read-next, also-read) — never headings, never a block holding the
  `h1` or half the page's paragraphs. After it, `_drop_repeats` removes a heading equal to the post
  title, repeated text blocks (≥40 characters, innermost blocks only, not list items) and repeated
  images. Known leftovers kept deliberately (no generic rule catches them): Cointelegraph's byline
  block, CoinDesk's "Make preferred on Google" link. Extraction is still fetch-on-open — see
  Resolved decisions → Article extraction stays on open.
- **Image fallback and article cleanup** _(2026-10-13)_ — backend. Ingest's `_pick_image` falls
  back to the first `<img src>` in the entry's content, then summary, after `media:thumbnail` /
  `media:content` / image enclosure, skipping declared widths under 480 and non-http sources
  (fixes WordPress feeds: 9to5mac 0 → 100 of 132 posts with images). `core/extract.py` drops
  text-less `<a>` elements wrapping an image and linking to another site (unless the link is an
  image file) before trafilatura; cached articles keep old markup until re-extracted.
  `proxy_images(html, lead)` drops the article's copy of the post's lead image when the post
  page shows it. 382 tests passing. See [images.md](./images.md) § Decision log.
- **Post images (T15a)** — every post image on screen comes from a signed `imgproxy` proxy
  (`docker-compose.yml`'s `imgproxy` service; nothing stored). `backend/core/images.py` is the
  only module that builds or signs such a URL — a containment test fails the suite if a second
  one reads an `IMGPROXY_*` setting, the rule `core/search.py` already follows for the tsvector
  — and its one entry point, `post_image(url)`, returns `{src, srcset} | null` for a 16:9 family
  (480 / 960 / 1440 / 1920, WebP, `rs:fill-down:…/g:ce/…` — a centre crop that shrinks the
  *requested* size to fit a small source rather than skipping the crop, which is what removes
  YouTube's `hqdefault` letterbox). An empty `IMGPROXY_KEY` is a supported state, like
  `YOUTUBE_API_KEY`: every `image` answers `null` and cards render compact. `PostSchema.image_url`
  is renamed to `image: {src, srcset} | null` on the wire (list, detail and `/search` all carry
  it, via the shared `PostPageSchema`); `app/components/feed/PostImage.vue` is the fixed
  `aspect-video` `bg-muted` box both hosts render it in — lazy on a card, eager with
  `fetchpriority="high"` on the post-page hero — and it removes itself on a failed load or a
  source narrower than 320px (a blown-up thumbnail reads worse than none) rather than leaving a
  broken box, resetting on an `src` change since the desktop post pane reuses one instance across
  posts. **A source that declares its own size answers `null` before any of that** _(2026-09-23)_:
  when the image URL carries a `width=` under 480 — the smallest size we serve — there is no
  image on the wire and the card is compact from the first paint. Reddit is why (207 of 477
  stored Reddit images declare 140, 216 or 320, and the size is inside the URL's signature so it
  can't be raised), and without it four cards in ten laid out a box and then took it away. The
  two floors are a pair until T15d reads real dimensions at ingest and retires both. See
  [images.md](./images.md).
- **Article images (T15c)** — the pictures inside an extracted article load through the same
  proxy, fit to the reading width with no crop (an author's own framing shouldn't be cropped to
  16:9) and no width floor (a small inline image is meant to be small; imgproxy never enlarges
  it). `backend/core/extract.py`'s `proxy_images` does the rewrite as a second `nh3.clean` pass
  at read time, over the same allowlist — never into the cached `article_html` column, so a key
  rotation can't break every cached article. An image that can't be proxied (a relative or
  scheme-relative `src`, or every image when there's no proxy key) is dropped with its tag
  rather than left srcless for the browser to draw as broken. See [images.md](./images.md).
- **Feed icons (T15b)** _(2026-09-28)_ — every feed has a face in the add wizard: each
  `SearchStep.vue` row leads with a `UAvatar` for every type, showing the proxied icon or, when
  there is none or it fails to load, the name's initials (only words that start with a letter
  or digit count, so "Vue.js - The progressive…" is "VT", not "V-"). Which picture stands for a
  feed is `backend/core/icons.py`'s rule: Atom's `<icon>` only (RSS `<image>` and Atom `<logo>`
  are banners, and a square crop of one reads worse than initials), then the site's declared
  icons largest-first, then an unverified `/favicon.ico` guess. A YouTube channel's face is its
  page's `og:image` avatar — never YouTube's own icons or favicon, which are identical for every
  channel. Discovery reads the icon off the page it already fetched, at no extra request;
  ingest looks it up once per source when the icon is blank, and never again. `images.icon()`
  serves it as a signed 64 × 64 centre crop. Wire: `icon_url` became `icon: string | null` on
  `/home` sources and `/discover` results. **Not consumed anywhere else yet** — home rows, the
  feed page's source rows and the PostCard show no icon (the card uses a type icon instead). See
  [images.md](./images.md).
- **PostCard v2** _(2026-09-28)_ — `app/components/feed/PostCard.vue`, redesigned. The
  **Image** style (the account's default, Settings → Appearance → *Post cards*) is a **square
  thumbnail beside the text** (`FeedPostImage` with its `square` prop; 128px, then 160 / 176 /
  192 at `md` / `lg` / `xl`) with a **meta row** above the title — a type icon (YouTube, Reddit;
  a website gets an external-link icon) and the source's name as a link to its `site_url`, then
  `·` and the date — and a **3-line excerpt** of `summary`, with Reddit's "submitted by" footer
  and Hacker News's footer stripped. **Compact** — and any post with no image, under either
  style — is date + title alone. The card is no longer one big link: the title link is stretched
  over the whole card and the source link sits above it, so each is its own target; the card is
  `isolate`, which keeps that link's `z-10` from painting over the desktop pane's sticky title
  row. Rows are separated by spacing (no divider lines). Closes the old "source-feed type cue"
  item. **Surfaces** _(2026-10-08)_: the card rests on `bg-elevated`; selected and hovered
  (desktop pointers only, `hover-lift`) both go to `bg-muted` with no shadow — hover equals
  selected on purpose. The meta row's source link is always underlined, here and on the post
  page. **Source on the post** _(2026-10-08)_: the shared meta row (`feed/PostMeta.vue`) reads
  `post.source` — name, type, site — straight off the post, with no store lookup, so it still
  names a saved post's source after that source has left every feed (it used to fall back to
  the date alone).
- **Reading-pane split (desktop)** _(2026-09-28)_ — `UserSettings.pane_split`
  (`posts` / `equal` / `post`, default `equal`) gives the posts and post panes 60/40, 50/50 or
  40/60. It rides `GET` / `PUT /settings` and the settings store; Settings → Appearance has a
  **Reading panes** section (desktop only), and `desktop/Shell.vue` applies `basis-3/5`,
  `basis-1/2` or `basis-2/5` to the posts pane while the post pane takes the rest. The
  Settings/Add in the post pane are unaffected (held to `--container-reading`).
- **YouTube in the reader** _(2026-09-28)_ — the Post API carries `video: {src, vertical} | null`,
  built from `post_url` by `core/youtube.video()`: a `youtube-nocookie.com` embed
  (`playsinline=1`, `rel=0`), `vertical` meaning a `/shorts/` link. `feed/PostVideo.vue`
  replaces the image slot on the post page; a Short gets a 9:16 box at 70svh (the `video-short`
  `@utility` in `layout.css`). A video post shows its description with line breaks kept and no
  inline **Open source** link — the action bar already has one.
- **Sharper images** _(2026-09-28)_ — at ingest a YouTube `hqdefault` thumbnail is swapped for
  `hq720.jpg` when a `HEAD` request finds it (answer cached 30 days; a network failure is not
  cached), and a Reddit `preview.redd.it` thumbnail becomes the `i.redd.it` original
  (`external-preview.redd.it` is left alone). `FeedPostImage` has a `noUpscale` prop, used on
  the post page, capping the box at the image's natural width.
- **Tooltips and Escape** _(2026-10-09)_ — every `IconButton` shows its `aria-label` as a
  hover tooltip (`UTooltip`, styled once in `app.config.ts`, since 2026-10-23 as bare muted 11px text, desktop only;
  `<UApp>` sets a 400ms delay and keyboard-focus-only, so touch never shows one), and so does
  the feed title's info icon. **Escape** in the post list's search box closes it and clears
  the search, like its X. The card excerpt also strips Hacker News's text-post footer
  ("Comments URL: … Points: … # Comments: …" with no Article URL in front), which used to show.
- **Polish pass** _(2026-10-08)_ — frontend only; no new feature. Post card surfaces, the shared
  meta row and the post page order are under PostCard v2 and Post page v1 above. **Desktop sticky
  pane-top rows** (the posts list's title/search row, the post pane's action strip) end in
  `pb-sm`, so content never scrolls flush against the buttons; the content below takes the
  remainder (`lg:mt-xs` on the list, `lg:mt-sm` on the post title). **Motion has one home**,
  `app/assets/css/motion.css`: Tailwind's transition defaults set to 250ms ease-out (Nuxt UI's
  transitions included) and `--duration-slide` / `--ease-slide` for the slides, read by
  `transitions.css` and `utils/panel-slide.ts`; every `duration-*` / `ease-*` class is gone from
  app code, which now never writes them (the old mix of 200 and 300ms became 300, then 250 _(2026-10-13)_) — see
  [design-system.md](./design-system.md) § Motion. **Add wizard**: `.slide-panels` is now
  `position: relative; overflow: hidden`, so a leaving step no longer escapes to the whole
  desktop overlay for a frame, and the desktop wizard renders its step swap with `:css="false"`
  (no transition phase at all).
- **Context-aware navbar** — both slots swap per page: home = menu + add, post list =
  sidebar icon (→ home) alone (search sits on the list's title row instead — see Post list v1),
  post page = back (→ its feed, carrying the search it was opened from) + Copy link + Open
  source + Save (`FeedPostActions` — see Post page v1). The feed page and its views carry
  their own header (back, plus the edit pencil on the feed page) instead of the navbar.
  Navigation is hierarchical, not history-based.
- **Reader slide transitions** — **mobile only** (the desktop shell renders no `<NuxtPage/>`,
  so this machinery never runs there — see Desktop shell v1). home → feed → post — and
  feed → feed page → its edit / source views — slide like a
  navigation stack (deeper pushes in from the right, back pops out to the right). Direction is
  set on route meta by `app/middleware/page-slide.global.ts` (computed *before* render — a
  component watch is one navigation late), shared `.page-slide-*` classes live in
  `assets/css/transitions.css`, and the default layout provides the positioning/clip context.
  Non-reader routes (add, settings) swap instantly (`page-none`) so their drawer animations own
  the motion; the settings drawer's internal slides — and the add wizard's, and this
  middleware's own direction check — share one push/pop rule and its CSS variables in
  `app/utils/panel-slide.ts` (`panelSlideDirection`/`panelSlideVars`, replacing three copies of
  the same logic). An **equal-depth** move (one settings panel to a sibling) now slides **not at
  all**, rather than incorrectly animating as a push — the bug the consolidation fixed.
- **Swipe navigation** — `app/composables/useSwipeNav.ts` (VueUse `useSwipe`, touch-only).
  `useSwipeBack`: swipe right anywhere on the post list, post page, the feed page and each view
  under it, or a settings subpage drags the page with the finger and past 72px pops to the
  parent route (reusing the page-slide / panel-slide pop); under threshold it snaps back.
  Axis-locked so vertical scrolling and vaul's drag-to-close are untouched; back buttons
  unchanged. _(An earlier version of this entry listed a `useSwipeOpen` — swipe left on a row
  to open it. It is not in the tree; corrected 2026-10-08.)_

## Stubs (exist but placeholder content)

- **Add-feed search by keyword, outside YouTube** — pasting a URL of any kind resolves for real
  (T11a), and a channel name under the YouTube card searches YouTube (T11b) — see Built, and
  [backend-roadmap.md](./backend-roadmap.md). What's still a stub is a **keyword under Website
  or Reddit**: subreddits by name is T11c, our own catalog T11d. Until then those two cards report
  "Nothing found. Try pasting a link."

## Not started

- **Desktop polish** — v1 (see Built → Desktop shell v1) ships the structural three columns
  only: keyboard focus rings still globally suppressed. Auto-selecting
  a detail post (e.g. the last-read one) on entering a feed is also deferred — v1 always starts
  with no post open: the feed page in the post pane, or on Home and Saved the "Select a post"
  placeholder.
- **Settings content** — the drawer, its five subpages (Shortcuts desktop only), and transitions are built, and
  Appearance and Account are real, including the Post cards switch (see Built); About's version
  string is hardcoded and Report still needs real content and a way to actually send anything.
- **Add feed (rest)** — keyword search for subreddits and our own catalog (T11c, T11d), a
  candidate's latest posts before adding it (T14, planned — `GET /discover/posts`), putting the
  wizard's type and query on the URL so a reload doesn't lose them (decided 2026-09-18, deferred
  to T14 — see [backend-roadmap.md](./backend-roadmap.md) § Decision log), sub counts, and input
  validation via VeeValidate/Zod. The wizard UI, RSS discovery from a pasted URL, YouTube search
  by name and the add itself (into a feed or a New feed) are built (see Built) — any URL works
  end to end.
- **Saved posts (rest)** — saving, unsaving and reading the saved streams work end to end (see
  Built), but every save lands in **Bookmarks**: there is no group chooser and no way to move a
  post between Bookmarks / Favorites / Later, though the API call for it is the same upsert.
- **Sign-in (rest)** — Google sign-in works end to end (see Built → Auth & login), but the
  **dev-token field is still on `/login` for everyone**, deliberately: the natural retirement is
  gating it on `import.meta.dev`, and gating it at build time today would make it vanish silently
  the day a production deploy exists. No native Google sign-in either — the Capacitor plugin is
  the other half of [backend.md](./backend.md#auth) § Auth's step 1, and no Capacitor build
  exists yet. Noted for a deploy: `ux_mode: 'popup'` needs a
  `Cross-Origin-Opener-Policy: same-origin-allow-popups` header if one is ever set.
- **Images (rest)** — T15a shipped post images on cards and the post page (see Built → Post
  images), T15c the pictures inside an extracted article (see Built → Article images), and
  T15b feed icons in the add wizard (see Built → Feed icons). Stage 2 (originals in a bucket,
  for permanence, T15d) and stage 3 (a CDN and a paid transformer at deploy, T15e) come after.
  The whole strategy, staged, is [images.md](./images.md); task entries in
  [backend-roadmap.md](./backend-roadmap.md) § Tasks → T15d, T15e.
- **Home reorder** — `PUT /home/order` exists and is strict (it now takes **feed uids only** —
  the whole flat list, nothing else to interleave), but **nothing drives it**: the home list has
  no drag-and-drop and no other way to move a feed, and the `feeds` store has no action for
  it. Feeds arrive from `/home` already in display order, so the UI, when it lands, writes the
  new order and swaps the list locally or re-reads `/home`.

## Installed but unused

- **VeeValidate + Zod** — not wired into any form yet.
- **@vueuse/motion** — available for animations.

## Open decisions

_None currently._

## Resolved decisions

- **Feeds are groups of sources** _(2026-10-08)_ — **no folders.** The user's call: "lets not
  have folders. we simple have feeds and sources. feed is like a folder, its a group of sources.
  feed has title description and list of sources. feed can also have a single source." Settled
  with it: **one source can sit in several feeds**; sources can be **renamed** (per feed) and
  their **links changed**; adding a source asks **which feed it goes into, or "New feed"**; and
  existing data was a **fresh start** (old feeds and folders dropped, saved posts kept). On/off
  per feed replaces the old per-folder mute. The shape of a feed's own page came from a
  screenshot of crowdfeed, the user's earlier aggregator. Consequences for the docs: `Source` is
  now a user-facing noun (`source_*`), so "a `Source` is never named on screen" no longer holds
  (full reasoning in [backend.md](./backend.md) § Decision log, 2026-10-08); "feed page" now
  means a feed's own page, and the post-list screen the docs used to call that is the **post
  list**. This supersedes **Folders** (2026-06-30) and **Folder reads through the feed page**
  (2026-07-01) below, and amends **Saved groups** (2026-07-11).
- **Article extraction stays on open** _(2026-10-23)_ — the user chose to keep extracting when a
  post is opened, not in the background at ingest. The post page shows title, meta and image at
  once and the body after. Extracting at ingest would fetch articles nobody opens (see
  [backend.md](./backend.md) § Decision log).
- **Images** _(recorded 2026-09-15)_ — every image the app shows goes through a proxy the
  backend signs URLs for; the frontend never builds one. Staged so the first hundred readers
  run on one server and growth is bought, not rewritten: `imgproxy` with nothing stored, then
  originals in a bucket, then a CDN / paid transformer — each a change inside
  `core/images.py`. Cards come in two versions (image / compact) behind a synced
  Appearance setting; the post page gets a 16:9 hero (the card layout was later reshaped to a square beside the text, 2026-09-28). Pre-rendering sizes at ingest — the
  previous project's shape — was rejected because a new size then means a backfill. Full
  reasoning in [images.md](./images.md) § Decision log.
- **Post search presentation** _(recorded 2026-09-15)_ — the question T12 left open (mobile
  sheet vs. centered dialog) is settled as **neither**: the search box swaps in for the list's
  title on the same row, in `FeedPostList.vue`, so the mobile feed page and the desktop posts
  pane share one entry point. The query lives on the route as `?q=` (debounced, `replace` not
  `push`), which is what makes a deep link, a reload, and Back from a post all land on the same
  results. See Built → Post list v1.
- **Desktop motion** _(recorded 2026-09-15)_ — **nothing slides on desktop.** The content area
  (Settings / Add) replaces the post pane's content the way a new page would, the add wizard's
  steps cut, and detail-pane swaps were already plain. Sliding is the mobile stack's language:
  there one pane is the whole screen and the motion says which way you moved; on desktop both
  ends of a move are on screen at once, so it would only be decoration. This closes the "no
  desktop pane/overlay transitions" item that Desktop polish carried as a gap.
- **Desktop layout composition** _(2026-07-27)_ — desktop (≥1024px) is **three columns**
  (sidebar + posts pane + post pane), composed by `app/layouts/default.vue` /
  `DesktopShell` straight from the existing routes and the `feeds`/`settings` stores —
  **not** a nested-`<NuxtPage/>` master/detail tree (tried twice; a child navigation
  under a nested page remounts the parent, nuxt#13094 — see
  `.claude/memory/project-gotchas.md`). On desktop, no route renders a `<NuxtPage/>` at
  all; the routes and `pages:extend` records are unchanged, so the mobile tree still
  works exactly as before. This settles the "Routing scheme" decision below toward
  layout-composed panes rather than nested routes for the desktop half of that promise.
- **Desktop breakpoint** _(2026-07-27)_ — a single 1024px tier (Tailwind `lg`) for v1:
  below it the app is the mobile structure, at or above it the desktop shell. A
  middle tablet tier is possible later but not built.
- **Desktop detail-pane selection** _(2026-07-27)_ — the post pane shows a placeholder
  ("Select a post") until a post is clicked; there is no auto-select of the first or
  last-read post. Revisit later if that feels wrong in daily use. **Amended _(2026-10-08)_:**
  until a post is clicked the pane shows the feed's own page instead; only All feeds, which has
  none, keeps the placeholder. Still no auto-select.
- **AI reading-companion feed** _(2026-07-16)_ — a custom RSS feed of AI-written posts
  (one per book chapter, reflection + link back to the chapter) is specced in
  [ai-feed.md](./ai-feed.md). Lives in a separate `feedme-books` repo (Python; batch
  generation → manual review → all-at-once or daily-drip release rebuilding `feed.xml`);
  zero FeedMe changes — it's just another Source once the backend lands. Nothing is
  implemented yet.

- **Backend stack & API** _(2026-07-12)_ — the fetching + persistence stack is specced in
  [backend.md](./backend.md): Django + django-ninja + Dramatiq + Postgres + Redis in
  `backend/` (monorepo, Docker Compose). Global shared sources polled once, per-user
  Feed/Folder/SavedPost/Settings layer, Google OAuth with opaque bearer tokens, Postgres
  FTS + trigram search behind an engine-neutral `/search`, on-demand article extraction,
  ~90-day retention for unsaved posts. Endpoint catalog and decision log live there.
  **Hello world is running** _(2026-08-07)_: `backend/` is a Django 5.2 + django-ninja
  project (package `feedme`) with one endpoint, `/api/v1/health`, ninja's auto-generated
  docs at `/api/v1/docs`, an OpenAPI schema at `/api/v1/openapi.json`, and Django admin at
  `/admin/`. `docker-compose.yml` at the repo root runs `api` (port
  8000, code bind-mounted), `db` (Postgres 16, healthchecked, `pgdata` volume), and `redis`;
  `worker`/`scheduler` joined the stack in T9 _(2026-09-03)_ — see below. `.env.example` is at
  the repo root.
  **Models are in** _(2026-08-07)_: the Django app `backend/core/` implements
  [backend.md](./backend.md)'s § Data model exactly — all 9 tables (custom `core.User` as
  `AUTH_USER_MODEL` with a unique nullable `google_sub` and email login, `AuthToken`,
  `Source`, `Post`, `Feed`, `Folder`, `FolderMember`, `SavedPost`, `UserSettings`), the
  spec's unique constraints and cascade/`PROTECT` rules, and uid minting via
  `core/uids.py`'s `make_uid(prefix)` (the backend mints `source_*`/`post_*`/`feed_*`/
  `folder_*`, per the vocabulary table). All models are covered by Django admin (Source
  gets the ops treatment — active/error-count visibility; **reshaped 2026-09-01** so that
  settings, feeds, folders, saved posts and sessions are edited as inlines on the user's own
  page and only the global tables are listed on the index). One migration
  (`core/migrations/0001_initial.py`), an idempotent `ensure_superuser` management command
  driven by `DJANGO_SUPERUSER_*` env vars, and a dev `entrypoint.sh` (migrate →
  ensure_superuser → runserver) wired into the Dockerfile. Verified: full stack bootstrap
  from an empty volume, an ORM smoke test of every model + its cascades, `/api/v1/health`
  200, admin login page serving. Still not built: API endpoints beyond `/health`, the auth
  guard, Google OAuth, the fetching pipeline/Dramatiq, and search (tsvector/GIN/trigram,
  deferred to a dedicated search session) — everything else `backend.md` specs is still the
  agreed target, not built. **Sequenced _(2026-08-19)_:** the remaining work is split into 13
  dependency-ordered tasks in [backend-roadmap.md](./backend-roadmap.md), starting with CORS +
  the test harness, then bearer-token auth, and reaching a deliberate checkpoint at T6 where
  the Nuxt app is wired to real data before the backlog grows further.
  **T1 landed _(2026-08-19)_:** CORS via `django-cors-headers` (allowed origins from
  `CORS_ALLOWED_ORIGINS`, defaulting to `http://localhost:3000`, middleware first in the chain),
  `ruff` + `pytest`/`pytest-django` configured in `backend/pyproject.toml`, a `user` fixture in
  `backend/conftest.py`, and `backend/tests/` covering `/health`, CORS preflight (allowed and
  foreign origin) and the custom user model. `SECRET_KEY` now raises `ImproperlyConfigured`
  instead of silently using the dev key when `DEBUG` is off. Verified: `pytest` green in the
  container, `ruff check` clean, and a real `fetch()` from a page on `localhost:3000` reaching
  `/api/v1/health` with no CORS error.
  **T2 landed _(2026-08-23)_:** the API is now login-only. `backend/core/auth.py` mints
  opaque tokens (`secrets.token_urlsafe(32)`, stored SHA-256-hashed, sliding 30-day window
  measured from `last_used_at` and touched at most hourly) and its `BearerAuth` guard is wired
  globally via `NinjaAPI(auth=…)`. `/health` is the one `auth=None` opt-out, and now backs a
  compose healthcheck on the `api` service. Endpoints moved into `backend/core/api/`:
  `account.py` serves `GET /me` (email, member-since, provider — the three lines
  `settings/Account.vue` hardcoded at the time), `DELETE /me` and `POST /auth/logout`, and
  `errors.py` holds the single `{"detail": string}` error body. `manage.py issue_token
  <email>` prints a usable token, so every later endpoint is testable before Google OAuth
  lands in T8. Verified: 21 tests green, `ruff` clean, and a real curl loop — 401 without a
  token, 200 with one, 204 on logout, 401 again straight after.
  **T3 landed _(2026-08-25)_:** the database holds real posts. `backend/core/ingest.py`
  exposes one synchronous `ingest_source(source)` — conditional GET with `requests` (explicit
  connect/read timeout, `If-None-Match` / `If-Modified-Since` from the stored validators),
  early return on 304, `feedparser` on the bytes, then upsert by `(source, guid)` so a re-poll
  updates a post in place and keeps its `post_*` uid. Entry mapping covers all three source
  types: `media:thumbnail` for YouTube posters, image enclosures for blogs, `published` over
  `updated` for the timeline. Failures never raise — `error_count` climbs, `next_fetch_at`
  backs off exponentially to a 24h cap, and the source deactivates after five in a row, with a
  **Reset errors and poll on the next run** admin action as the way back. Driven by
  `manage.py poll_source <source_uid>` and `manage.py poll_due`; T9 wraps the same function in
  a Dramatiq actor. Verified: 50 tests green, `ruff` clean, and the three mock sources polled
  for real — 10 Medium + 15 YouTube + 25 Reddit posts, a second `poll_due` correctly reporting
  nothing due, and a manual re-poll returning 0 new / 25 updated. Next is T4 — `/home` and
  `/settings`.
  **T4 landed _(2026-08-25)_:** the app's cold-start round-trip and account-level preferences
  are real. `backend/core/api/home.py`'s `GET /home` returns one aggregate — folders, every
  feed (with `Source`'s `type`/`site_url`/`feed_url`/`icon` flattened onto it, `type` typed
  as a `Literal` matching `app/assets/types.ts`'s hand-written `FeedType` union, so `source_uid`
  never leaks), the shared top-level order, and saved counts — in a constant 5
  queries no matter how many feeds an account has; `PUT /home/order` writes the one shared
  0..n-1 sequence across `Folder.order` and `Feed.order` in a transaction, and strictly rejects
  (422, naming the offending uids) a duplicate, a foreign uid, a folder-member uid, or a
  top-level uid left out, writing nothing on failure. `UserSettings` gained `scrollbar_style`
  (dropped again in migration 0008, 2026-10-21; migration `0003_usersettings_scrollbar_style.py`, mirroring `app/stores/settings.ts`'s
  `thin`/`comfortable`/`auto`); `backend/core/api/settings.py`'s `GET`/`PUT /settings` read and
  fully replace it, `theme`/`feed_list_style`/`scrollbar_style` typed as `Literal` unions, with
  `GET` answering from an unsaved instance rather than creating a row on read. Verified: 76
  tests green (was 51), `ruff` clean, and against the real dev database — `/home` returning the
  three real feeds and a folder (one member muted) with correct top-level ordering, a reorder
  round-tripping through `PUT /home/order`, all three 422 branches firing correctly, and
  `/settings` returning defaults with no row then round-tripping through a `PUT`. Next is T5 —
  posts: list, detail, save.
  **T5 landed _(2026-08-26)_:** the posts are readable. `backend/core/postlist.py` owns the
  polymorphic uid in the frontend's own order — `all` → `saved` → `saved_*` → `folder_*`
  (members minus the ones muted in *that* folder) → `feed_*` — plus the base64 keyset cursor
  and the rule for which posts a caller may open at all: one from a source they subscribe to,
  or one they have already saved, so a saved post stays readable forever after unsubscribing.
  `backend/core/api/posts.py` serves `GET /feeds/{uid}/posts` (`?cursor=&limit=`, default 10,
  capped at 100, newest-first) in a constant **2 queries whatever the page size** — the caller's
  sources and the three fields that depend on who is asking (`feed_uid`, `saved_group`,
  `saved_at`) are correlated subqueries rather than joins. `feed_uid` resolves the global source
  to *your* feed and is `null` when you no longer have one; `saved_group` is `null` until you
  save, so a card renders its save state without a second request. Saved lists order by
  `saved_at`, everything else by `published_at`. `GET /posts/{uid}`, `PUT /posts/{uid}/save`
  (an upsert — moving between groups is the same call, and `saved_at` survives the move) and
  `DELETE /posts/{uid}/save` (idempotent, so a double-tapped toggle is a no-op) round it out.
  Verified: 108 tests green (was 76), `ruff` clean, and against the real dev database — paging
  the 50 real posts eight pages at a time with no repeat and no skip, every uid branch returning
  the right set, a save round-trip that `/home`'s `saved_counts` agrees with, and
  `/api/v1/openapi.json` carrying `feed_uid: string | null` and the `saved_group` union that T6
  generates TypeScript from.
  **T6 landed _(2026-09-01)_:** the frontend runs on this API — the checkpoint the roadmap was
  built around. Sign-in is a dev token on a new `/login` screen, proven against `/me` before
  it's kept; `app/plugins/api.ts` is the single `$api` instance that attaches the bearer and
  turns a 401 into a redirect; the `feeds` store loads `GET /home`; `usePostList(uid)`
  cursor-pages `GET /feeds/{uid}/posts` behind an intersection sentinel; `usePost(uid)` reads a
  post and toggles `PUT`/`DELETE /posts/{uid}/save`; the `settings` store round-trips
  `GET`/`PUT /settings`; and Settings → Account shows the real `/me` profile with a working
  Sign out. Types are generated from the OpenAPI document into `app/types/api.d.ts`
  (`pnpm types:api`), with `app/assets/types.ts` reduced to aliases over it, so the two sides
  can no longer drift. `app/assets/data.ts` and `app/assets/mock-search.ts` are **deleted** — no
  fallback path. Four decisions worth knowing, all in
  [backend-roadmap.md](./backend-roadmap.md) § Decision log (2026-09-01, T6): SSR renders the
  shell but **every API call is client-only** (the token never reaches the Nuxt server, which is
  how Capacitor will behave); the account's data loads in `app.vue`'s `onMounted`, **not** in
  middleware, because filling the stores before the hydration render is a real mismatch against
  a server render done on empty stores; each store captures `useNuxtApp()` at setup, since an
  action can run past an await where no Nuxt context exists; and the open post is fetched by its
  host rather than through a shared `useAsyncData` entry, which the mobile/desktop swap at the
  `lg` breakpoint clears out from under the survivor. An unreachable API is its own state
  ("Can't reach the server" + Try again), never the first-run empty state. Verified: `pnpm lint`
  and `pnpm typecheck` clean, and against the running API — sign-in on both viewports, all five
  post-list uid branches, paging 50 posts with no repeats, a save surviving a reload, the
  settings round-trip, sign-out revoking server-side, and the 401 redirect. Next is T7 —
  subscribe and folder writes.
  **T7 landed _(2026-09-01)_:** the app writes. `backend/core/api/feeds.py` adds `POST /feeds`
  (`{feed_url, folder_uid?}`) — find-or-create the global `Source`, with its `type` inferred
  from the host rather than taken from the request, and for a **brand-new** source run T3's
  `ingest_source()` **inline**, because fetching the feed is the only honest way to know a URL
  is one; on failure the source row is deleted again and the caller gets a 422 ("That URL isn't
  a feed."), so a typo leaves no dead global row. A source that was deactivated when its last
  subscriber left is reactivated instead. `PATCH /feeds/{uid}` renames (name only, contract
  resolution 3) and `DELETE /feeds/{uid}` unsubscribes — memberships cascade at the database
  level, and the source is then deactivated rather than deleted, because its posts and other
  readers' saves outlive your subscription. `backend/core/api/folders.py` — tagged **`home`**,
  since a folder is home-screen structure — adds `POST /folders`, `PATCH /folders/{uid}` (name,
  members and mutes each optional, so the folder panel's single Save is a single call) and
  `DELETE /folders/{uid}`, returning the same `unsubscribed_count` the confirm sheet predicted.
  Both obligations T4 left behind are settled there: a membership write verifies every feed uid
  belongs to the caller, and a feed freed from its last folder is rehomed to the end of the
  top-level order. `PUT /home/order` now reads, validates and writes inside one transaction
  under `select_for_update()`, closing T4's recorded review note. On the frontend every
  `feeds`-store write calls the API — optimistic with rollback, except the two creates, which
  await the server-minted uid — the add wizard subscribes a pasted feed URL for real and shows
  the API's refusal on the destination step instead of closing, and the edit drawer's copy,
  aria-labels and route segments (`/edit/:uid/feed/:feedUid`) moved onto
  [backend.md](./backend.md)'s vocabulary. Eight decisions are recorded in
  [backend-roadmap.md](./backend-roadmap.md) § Decision log (2026-09-01, T7). Verified: 159
  backend tests green (was 108), with a test per cascade rule, `ruff` clean, `pnpm lint` and
  `pnpm typecheck` clean, and the flow driven in a real browser at both viewports — subscribe by
  URL with the real title backfilled, the not-a-feed 422 leaving no source behind, rename,
  rename + mute in one save, all three cascade rules with their counts, re-subscribing
  reactivating a deactivated source, and an offline write rolling back.
  **T8 landed _(2026-09-03)_:** sign-in is real. `POST /auth/google` verifies the id_token Google's
  button returns (`backend/core/google_auth.py`, `google-auth` — signature, issuer, audience,
  expiry, and a verified email) and answers with **our bearer token alone**; the profile still
  comes from `/me`. An account is found by `google_sub`, else linked onto a row with the same
  verified email **that no Google account has claimed** (a claimed one is a 401 — an email can be
  reassigned, a `sub` can't), else created. On the frontend `/login` renders Google's button above
  the dev-token field and `signInWithGoogle()` hands its token to `signInWithToken()`, so there is
  one path after "set the token". **The dev path stays** — a deliberate reversal of T8's own plan
  and of the T6-era decision that promised its deletion; see
  [backend-roadmap.md](./backend-roadmap.md) § Decision log (2026-09-03, T8) for that and ten
  more, including why `provider` describes the account rather than the session, why a changed
  Google email never rewrites the stored one, and the two layout decisions Google's button chrome
  forced.
  Verified: 172 backend tests green (was 159, 13 of them new for sign-in), `ruff` clean, and the
  screen driven in a real browser — a rejected credential reported on the button's own line while
  a live session and its route stay untouched, and the button's chrome measured there rather than
  guessed. Next is T9 — Dramatiq, `worker`, `scheduler`.
  **T9 landed _(2026-09-03)_:** polling runs on its own. `backend/feedme/broker.py` is the one
  module that knows Dramatiq exists — it calls `django.setup()` (load-bearing for the
  `dramatiq`/`periodiq` CLIs, a no-op under `manage.py`), builds a
  `RedisBroker(url=settings.REDIS_URL)`, and adds periodiq's `PeriodiqMiddleware` plus a
  hand-written `DjangoConnections` middleware that closes stale per-thread database connections
  around every message, since nothing in a worker fires Django's request-started/finished
  signals. `backend/core/tasks.py`'s `poll_source(source_uid)` wraps T3's `ingest_source`
  unchanged (`max_retries=3`, a 2-minute time limit) and returns quietly — no exception — on a
  uid whose source has since been deleted or deactivated, because Dramatiq's retries cover only
  what can throw; a dead feed already has its own `error_count`/backoff, and the two error
  models deliberately don't overlap. `poll_due_sources()` is periodiq's cron sweep (every 5
  minutes, targeting the ~30-minute per-source cadence) — it **claims** its batch with a plain
  `update()` before sending, since `ingest_source` only pushes `next_fetch_at` out when a poll
  *finishes*; without the claim, a sweep would re-enqueue everything still queued or in flight.
  `backend/core/ingest.py`'s write phase (`_upsert_posts` → `_backfill_source_metadata` →
  `_record_success`) now runs inside one `transaction.atomic()`, so a worker killed mid-poll
  leaves nothing half-written. `docker-compose.yml` gained `worker`
  (`dramatiq core.tasks --processes 2 --threads 4`) and `scheduler` (`periodiq -v core.tasks`),
  sharing `api`'s image through a new `x-backend` YAML anchor so the three can't drift apart;
  both skip the migrate/bootstrap entrypoint and wait on `api`'s healthcheck instead, since only
  `api` should touch the schema. `manage.py poll_source`/`poll_due` survive as the manual
  override, and `POST /feeds`'s inline fetch (T7) was deliberately left alone — validating a
  brand-new subscribe is still a synchronous request. Eight decisions are recorded in
  [backend-roadmap.md](./backend-roadmap.md) § Decision log (2026-09-03, T9), including the two
  error models, the claim-before-send reasoning, and why plain `dramatiq[redis]` was chosen over
  `django-dramatiq`.
  Verified: 182 backend tests green (was 172), `ruff check` clean, and against the running
  stack — the scheduler fired unattended, enqueueing 4 due sources the worker polled across its
  threads in under 2 seconds (70 → 129 posts, all four rescheduled with jitter); a `SIGKILL` sent
  mid-poll against a deliberately slow feed left the source with zero posts and `error_count`
  untouched, and the redelivered message polled cleanly after the broker's heartbeat window; a
  `SIGTERM` let the in-flight poll finish before shutting down; and `POST /feeds` still validates
  inline exactly as T7 left it.
  **T10 landed _(2026-09-05)_, on the server only:** `GET /posts/{uid}/article` extracts a post's
  article on the first request for it and serves everyone from `Post.article_html` after — the
  cache is global because the post row is. It reuses T5's visibility rule, so a post you neither
  follow nor saved 404s as detail does. Extraction runs **synchronously with a hard timeout**
  inside the request rather than as a Dramatiq job, which **reverses**
  [backend.md](./backend.md) § Fetching pipeline's `extract_article` job row: the reader is
  blocked either way, and queueing would add a polling loop and a third state on screen for a
  slow path that runs once per post (measured: 0.99s first call, 0.012s second).
  `backend/core/extract.py` mirrors `ingest.py`'s shape — one network function, one entry point
  that never raises — and pipes trafilatura's HTML through `nh3.clean` with our own allowlist,
  because the frontend will render that field as markup and the guarantee has to be ours rather
  than a property of trafilatura's internals. The column keeps three states (`null` untried, `''`
  read-but-empty, the article) where the wire carries two (`ok` / `unavailable`), and **anything
  short of an article is retried on the next open** — `''` as much as `null` _(amended after
  T10, in the tree committed 2026-09-15; T10 itself cached the empty read)_: a bot-challenge page
  served as 200 or a site mid-deploy reads as empty once, and one bounded fetch per open is cheap
  next to a post that is wrong for every subscriber forever. The `''` is still stored so admin
  can tell "tried, empty" from "never tried". The fetch itself refuses non-public targets on every redirect hop, caps the body at
  2MB and rejects non-HTML, since unlike ingest this endpoint hands what it downloads back to the
  caller. Eight decisions — including that SSRF check's stated DNS-rebinding limit, the YouTube
  short-circuit, and why `favor_precision` is off — are in
  [backend-roadmap.md](./backend-roadmap.md) § Decision log (2026-09-05, T10).
  Verified: 208 backend tests green (was 182), `ruff check` clean, and driven against live pages —
  a blog post extracted in 0.99s and served from the column in 0.012s, a YouTube post answered
  `unavailable` in 0.010s with no outbound request, and Reddit's JS interstitial correctly stored
  as "read it, no article". **The frontend was wired to the endpoint on 2026-09-18** — `usePost`
  fires it alongside `GET /posts/{uid}`, and `FeedPostView` renders `article_html` as markup,
  falling back to the stripped `summary` plus Open source when extraction can't produce one (see
  Built → Post page v1).
  **T12 landed _(2026-09-06)_, ahead of T11a and on the server only:** `GET /search?q=&scope=`
  searches inside any list the app can already read — the `scope` is the *same* polymorphic uid
  the post list takes, resolved by the *same* `core/postlist.py` resolver, so muting a feed drops
  it from that folder's results immediately with no re-index, another user's uid 404s, and the
  response is byte-for-byte a post page paged by T5's cursor. `Post.search` is a **persisted
  generated tsvector** (title weighted over summary, `english`), recomputed by Postgres in the
  statement that writes the row, so search is never stale and there is no sync pipeline;
  migration `0004_post_search.py` installs `pg_trgm` by hand first (`makemigrations` never emits
  an extension operation), then the column, then a GIN index on it and a **functional** trigram
  index on `upper(title)` — functional because Django compiles `__icontains` to
  `UPPER("title"::text) LIKE …` and the planner only matches an index built on the same
  expression. Nothing was installed to do any of it: `pg_trgm` is a Postgres extension and
  `django.contrib.postgres` ships with Django. Matching is two branches: full-text (`websearch`,
  so a stray quote comes back empty instead of 500ing) over title and summary, plus a title-only
  substring for the partial words FTS structurally can't reach — `summary` is never
  substring-matched, since it is third-party HTML and that would match markup. Results are
  ordered by **recency, not relevance** (the weights are in the vector, so ranking later is an
  `order_by`, not a migration), and a blank `q` is an empty page rather than a 422. All of it
  lives in `backend/core/search.py`, with a **test that scans `core/` and fails** if any other
  module touches the tsvector column — which is what keeps
  [backend.md](./backend.md#search)'s "swap in Elasticsearch by rewriting one module" promise
  checkable. Nine decisions are in [backend-roadmap.md](./backend-roadmap.md) § Decision log
  (2026-09-06, T12). Verified: 255 backend tests green (231 before, 24 new), `ruff check` clean,
  and against the real dev database — partial words matching real posts, every scope branch,
  a mute reflected instantly, 105 results paged two at a time across 53 pages with no duplicates,
  and `openapi.json` carrying `search_posts` under `feeds` with still exactly four tags.
  **The frontend is wired to it** — the feed page and the desktop posts pane search from their
  title row (see Built → Post list v1), and `app/types/api.d.ts` has been regenerated to carry
  the `/search` path.
  **T13 landed _(2026-09-07)_, with no endpoint and no screen behind it:** the posts table now has
  a ceiling. `backend/core/retention.py` holds every deletion rule — unsaved posts older than **90
  days**, and per source those beyond the newest **500**, both rules deleting, so a post goes if
  either catches it — and **a saved post is never deleted**, at any age and no matter who saved it,
  since a post row is global and an owner-scoped rule would empty another account's pile. The cap
  keeps its newest rows by excluding their pks rather than comparing against a boundary timestamp,
  which is what makes it exact when a source stamps a whole batch with the same second. Deletes run
  in batches of 1000 pks, and `--dry-run` is the real run inside a rolled-back transaction rather
  than a simulation, because the cap pass ranks whatever the age pass left behind. Two daily actors
  in `core/tasks.py` (03:30 and 03:45) wrap the plain functions the way `poll_source` wraps ingest,
  with `manage.py prune_posts --days --cap --dry-run` as the manual override; the second one,
  `prune_expired_tokens()`, deletes `AuthToken` rows past `core/auth.py`'s imported `TOKEN_TTL` and
  closes the forward reference T2 left. The one change outside the new module is that **ingest now
  respects retention's line**: `_upsert_posts` won't create a post the prune would delete that
  night, because the first live run watched an archive feed put 49 just-deleted posts straight back
  on the next five-minute sweep — the consequence being that a feed whose entries are all past the
  window subscribes successfully with zero posts. Nine decisions are in
  [backend-roadmap.md](./backend-roadmap.md) § Decision log (2026-09-07, T13). Verified: 285
  backend tests green (was 263, 22 new), `ruff check .` clean, and against the real dev database —
  a dry run that predicted 51 deletions and a real run that deleted exactly those 51, a saved
  200-day-old post surviving both, and the post list, the saved list and `/search` all correct
  afterwards.
  **Hardened alongside, in the same tree:** the writes now refuse what would have been a 500 or a
  silent truncation — a name with a NUL byte is a 422 (one `clean_name` shared by feed and folder
  writes, so the two can't disagree about what a name is), a `feed_url` past the column's 500
  characters is a 422 rather than a truncated fetch of a different URL, a double-tapped Subscribe
  that races past the exists-check is caught at the unique constraint and answered as the same
  "You already follow that feed.", an ingest that raises mid-subscribe deletes the new source
  row instead of leaving a dead one behind, and a brand-new source is created already claimed
  for the poll interval so the five-minute sweep can't poll it from the worker while the inline
  fetch is still running. `PATCH /folders/{uid}` is one transaction from the rename down, so a
  refused membership takes the rename back with it; `DELETE /me` deactivates every source the
  account was the last subscriber of, since the cascade is the one way feeds vanish without
  passing through unsubscribe; and a cursor carrying a naive timestamp is a 422. **316 backend
  tests green in the tree as committed** (T13's 285 plus T11b's 12 in `test_youtube.py` and the
  tests behind the hardening above), `ruff check .` clean.
  **The feeds remodel landed _(2026-10-08)_, outside the numbered tasks**, and supersedes the
  models and endpoints above where they differ: `Folder` and `FolderMember` are deleted
  (migration `0007_feeds_group_sources`, no data step — the old feeds and folders were dropped,
  saved posts kept), `Feed` is now the user's group (`name`, `description`, `order`) with
  `sources` many-to-many through a new `FeedSource` (`name` = the user's rename, `enabled`,
  `order`; unique per feed and source; `source` is `PROTECT`), and `Source` gained `description`,
  backfilled at ingest from RSS `<description>` / Atom `<subtitle>` and flattened to plain text
  (cap 1000). `GET /home` is `{feeds: [{uid, name, description, sources: […]}], saved_counts}`
  in display order; `PUT /home/order` takes feed uids only; `core/api/feeds.py` serves
  `POST`/`PATCH`/`DELETE /feeds` and `POST`/`PATCH`/`DELETE /feeds/{uid}/sources[/{source_uid}]`,
  each answering with the whole feed; `core/api/folders.py` and its three endpoints are gone.
  `core/postlist.py` resolves `all` → `saved` → `saved_*` → `feed_*` (a feed's stream is its
  enabled sources; `all` is sources enabled in at least one feed), a post may be opened or saved
  if its source is in any of the caller's feeds, and `PostSchema.feed_uid` became
  `source: {uid, name, type, site_url}`. `/discover`'s `already_subscribed` now means "in one of
  your feeds". Details and the reasoning are in [backend.md](./backend.md) § Decision log
  (2026-10-08); `tests/test_folder_writes.py` is deleted and the feed, home, posts, search,
  account and admin tests were updated to the new shape.

- **Feed discovery** _(T11a, 2026-09-06)_ — the add wizard's search step does real work: paste a
  URL and `GET /discover` turns it into feeds you can subscribe to. **T11 was split into four**
  (see [backend-roadmap.md](./backend-roadmap.md) § Status); T11a is the part needing no external
  accounts, and T12 was built ahead of it. A pasted URL is fetched once and either parsed as a feed
  or read for the `<link rel="alternate">` tags it declares. Two shapes drove the design and both
  came from pasting real URLs, not from the suite, which was green throughout: **a post URL**
  (`nuxt.com/blog/meet-nuxi`) declares no feed while the section index above it does, so the
  resolver **walks up the path** — nearest first, always reaching the site root, capped at three
  fetches, and only when the pasted page came up empty; and **YouTube closes `<head>` after
  ~700 KB of inline script**, declaring its title and `videos.xml?channel_id=…` link in the *body*,
  so the parser reads the whole document (8 ms on a 1.6 MB page — `HTMLParser` skips script bodies
  as CDATA). Failing all that, `/feed`, `/rss`, `/rss.xml`, `/atom.xml`, `/index.xml` are probed at
  the root, which catches static-site generators that ship a feed and forget the tag. T10's
  SSRF-guarded fetch moved out of `core/extract.py` into **`core/fetch.py`**, shared by both
  callers that hand a fetched body back to the requester — a forced move, not a tidy-up: discovery
  needs a different accept header, content-type allowlist and byte cap, and once those are
  arguments the function is no longer "the article page fetcher". No new dependency: `feedparser`
  answers "is this a feed", stdlib `html.parser` answers "where is the feed on this page". Nine
  decisions are in [backend-roadmap.md](./backend-roadmap.md) § Decision log (2026-09-06, T11a).
  Verified: 263 backend tests green (28 new in `test_discover.py`, 17 in `test_fetch.py` of which
  15 moved with the code), `ruff check` / `pnpm lint` / `pnpm typecheck` clean, and against live
  sites — a Nuxt post URL, two feeds off overreacted.io, three off github.blog, Hacker News, two
  YouTube handles in ~450 ms, and `r/vuejs`. **Known limitation:** Reddit answers **429** to
  repeated unauthenticated `.rss` fetches, so a subreddit can resolve on one search and not the
  next; app credentials (T11c) are the fix.
  **T11b _(2026-09-11)_ — YouTube by name.** A bare name under the YouTube card is a Data API
  `search.list` (`backend/core/youtube.py`, the one module that spends quota; `fetch_search` is
  its one network call), mapped to the same `videos.xml` candidate a pasted channel resolves to,
  with the channel avatar as its icon. Shaped by the quota — 10k units a day, 100 per search:
  every answer is **cached for a day** under a hashed, whitespace-and-case-normalised key, a
  failed search is not cached (an error would otherwise be served for a day), and at most five
  channels come back even when YouTube overshoots `maxResults` (seen live). Django's cache is
  now the same Redis the broker uses (`CACHES` in `settings.py`), with one standing rule —
  never `cache.clear()` against it, since on that backend it is `FLUSHDB` and the queues share
  the database; tests swap in locmem so they can. `YOUTUBE_API_KEY` is optional like the Google
  client id: without it a name finds nothing and a URL or `@handle` still resolves through the
  channel page, spending no quota either way. YouTube refusing to answer is a **503** ("YouTube
  search is unavailable right now."), never an empty list. Frontend: `SearchStep.vue` leads a
  YouTube row with its avatar (websites followed with T15b) and shows the 503 as an error rather than "Nothing found".
  The card decides what a bare name means — `one piece` is a channel search under YouTube and
  nothing under Website — and a keyword under the other two cards is unchanged (T11c, T11d).

- **Routing scheme** _(2026-06-29)_ — **nested routes**: posts nest under feeds
  (`/feed/[uid]/post/[postUid]`), settings subpages nest under settings (`/settings/*`). The
  route encodes navigation context. Scaffold files (`Feed.vue`, `[Post].vue`,
  `SettingsAccount/About` components) move to match the nested tree. See
  [screens-and-flows.md](./screens-and-flows.md). **Amended _(2026-07-27)_:** the
  desktop two-pane presentation this route nesting was meant to drive is instead
  composed by the layout from these same routes (see "Desktop layout composition"
  above) — the routes stayed exactly as this decision specced, only the desktop
  *rendering mechanism* changed.
- **Saved posts entry point** _(2026-06-29)_ — saved posts surface as a **Saved** feed pinned
  in the feeds list (no `saved.vue` screen, no navbar bookmark icon). Saving stays the toggle
  on the Post page. Routed as `/feed/saved`, reusing the feed-page component.
- **Folders** _(2026-06-30)_ — feeds can be grouped into named **folders**, **many-to-many** (a
  feed can be in several folders; loose if in none). Created from the navbar **+** menu; edited
  via a long-press / 3-dot context menu (rename, add/remove feeds, **per-folder mute**, delete).
  **Mute** is per-folder only. **Remove from folder** unlinks; **delete feed** unsubscribes
  everywhere; **delete folder** also unsubscribes its feeds except those in another folder (with
  confirmation). See [data-model.md](./data-model.md) (its Folder section was removed).
  **Superseded _(2026-10-08)_:** there are no folders — see Feeds are groups of sources.
- **Saved groups** _(2026-07-11, amended through 2026-10-21)_ — the backend keeps three fixed
  groups, **Bookmarks / Favorites / Later** (uids `saved_*`), and `GET /home` still returns
  `saved_counts`. The app dropped them: one pinned **Saved** row opens `/feed/saved` (every save,
  all groups merged), saving files into the default group, and no screen links to a group or shows
  its count (the `/feed/saved_*` lists still resolve). Undecided whether groups ever surface again.
- **Folder reads through the feed page** _(2026-07-01)_ — a folder is **not** its own route.
  The feed page (`/feed/[uid]`) is polymorphic: `uid` resolves in a fixed order — `saved` →
  folder (`folder_*`) → feed (`feed_*`) — exactly the pattern `saved` already established.
  Chosen over a separate `/folder/[uid]` tree to avoid duplicating the feed/post routes; the
  page stays thin by delegating to a `usePostList(uid)` resolver. If folders ever need
  folder-specific chrome, splitting out a dedicated route is a cheap, additive refactor. See
  [screens-and-flows.md](./screens-and-flows.md). **Superseded _(2026-10-08)_:** there are no
  folders; the polymorphic uid is now `all` → `saved` → `saved_*` → `feed_*`.
