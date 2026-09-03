# Backend Roadmap

The execution order for building the backend specced in [backend.md](./backend.md). That doc
says *what the server should be*; this one says **what to build next, in what order, and how
you know a task is done**. Peer to [current-state.md](./current-state.md), which snapshots the
whole app — this file is backend-only and task-shaped.

**How to use it:** read § Status, open the task it names, build it, then update § Status and
the task's checkbox. Everything a task needs is in its own entry — you should not have to
re-derive context from the spec to start.

Task order is dependency-driven, not preference. T1 and T2 unblock every endpoint; T6 is a
deliberate checkpoint that wires the real frontend before the backlog grows further.

## Status

**Last completed:** T9 — Dramatiq, `worker`, `scheduler` _(2026-09-03)_
**Next up:** **T10 — Article extraction**
**Roadmap written:** 2026-08-19

| # | Task | State |
| --- | --- | --- |
| T0 | Scaffold, models, admin | ✅ done _(2026-08-07)_ |
| T1 | Foundations — CORS, ruff, pytest | ✅ done _(2026-08-19)_ |
| T2 | Auth — bearer tokens, global guard, `/me` | ✅ done _(2026-08-23)_ |
| T3 | Ingest core (synchronous) | ✅ done _(2026-08-25)_ |
| T4 | `/home` and `/settings` | ✅ done _(2026-08-25)_ |
| T5 | Posts — list, detail, save | ✅ done _(2026-08-26)_ |
| T6 | Vertical slice — wire the Nuxt app | ✅ done _(2026-09-01)_ |
| T7 | Subscribe and folder writes | ✅ done _(2026-09-01)_ |
| T8 | Google OAuth | ✅ done _(2026-09-03)_ |
| T9 | Dramatiq, `worker`, `scheduler` | ✅ done _(2026-09-03)_ |
| T10 | **Article extraction** | ⬜ next |
| T11 | Discovery | ⬜ |
| T12 | Search | ⬜ |
| T13 | Retention | ⬜ |

## Current state

The stack runs: `docker compose up -d` brings up `api` (:8000), `db` (Postgres 16,
healthchecked), `redis`, `worker` and `scheduler` — the last two share `api`'s image (a compose
`x-backend` anchor) with the migrate/bootstrap entrypoint dropped, since only `api` should touch
the schema.

**Built.** Django 5.2 + django-ninja project `feedme` with one app, `core`. All nine models
from [backend.md](./backend.md) § Data model live in `backend/core/models.py` with the spec's
unique constraints and cascade / `PROTECT` rules, behind one migration. Django admin covers
every model, with the ops treatment on `Source` (active flag, error count, fetch timestamps)
and — since 2026-09-01 — everything a user owns edited from the user's own page rather than as
tables of its own (§ Decision log). Public uids are minted by `core/uids.py`'s
`make_uid(prefix)`. An idempotent
`ensure_superuser` command and `entrypoint.sh` (migrate → ensure_superuser → runserver) handle
dev bootstrap.

T1 added the floor the rest of the roadmap stands on: `django-cors-headers` (origins from
`CORS_ALLOWED_ORIGINS`, defaulting to the Nuxt dev server), `ruff` and `pytest` +
`pytest-django` configured in `backend/pyproject.toml`, `backend/conftest.py` with a `user`
fixture, `backend/tests/` covering health, CORS preflight and the custom user model, and a
`SECRET_KEY` that refuses to fall back to the dev key when `DEBUG` is off.

T2 closed the API to anonymous callers. `backend/core/auth.py` mints opaque tokens
(`secrets.token_urlsafe(32)`, stored SHA-256-hashed) and its `BearerAuth` guard hangs off
`NinjaAPI(auth=…)`, so every operation needs a bearer token except `/health`, which is
`auth=None` for the new compose healthcheck. Endpoint modules now live in `backend/core/api/`
— `account.py` (`GET`/`DELETE /me`, `POST /auth/logout`) and `errors.py` (the one
`{"detail": string}` error body). `manage.py issue_token <email>` prints a working token.

T3 put real posts in the database. `backend/core/ingest.py`'s `ingest_source(source)` does a
conditional GET with `requests` (explicit timeout), hands the bytes to `feedparser`, upserts
posts by `(source, guid)`, and on failure grows `next_fetch_at` exponentially before
deactivating the source at five consecutive errors. `manage.py poll_source <source_uid>` and
`manage.py poll_due` drive it by hand, and a **Reset errors and poll on the next run** admin
action is the way back from a deactivation. The three mock sources — Medium's Vue tag, the
YouTube channel, r/OnePiece — are in the dev database with 50 real posts.

T4 built the app's cold-start round-trip. `backend/core/api/home.py`'s `GET /home` returns
folders, every feed (with `Source` metadata flattened onto it), the shared top-level order, and
saved counts, in a constant 5 queries regardless of feed count; `PUT /home/order` writes the
one shared 0..n-1 sequence across `Folder.order` and `Feed.order` in a transaction, rejecting
with a 422 naming the offending uids on any duplicate, foreign, or folder-member uid, or a
top-level uid left out. `backend/core/api/settings.py`'s `GET`/`PUT /settings` read and replace
`UserSettings` — `theme` / `feed_list_style` / `scrollbar_style`, the last one new this task
(migration `0003_usersettings_scrollbar_style.py`) — typed as `Literal` unions; `GET` answers
from an unsaved instance when no row exists yet, so a read never causes a write.

T5 made the posts readable. `backend/core/postlist.py` owns the polymorphic uid — `all` →
`saved` → `saved_*` → `folder_*` (members minus muted) → `feed_*`, the frontend's order — plus
the base64 keyset cursor and the "may this caller see this post" rule. `backend/core/api/posts.py`
serves `GET /feeds/{uid}/posts` (`?cursor=&limit=`, default 10, capped at 100, newest-first) in
**2 queries regardless of page size**: the caller's sources and the three per-caller fields
(`feed_uid`, `saved_group`, `saved_at`) are all correlated subqueries, not joins. `GET /posts/{uid}`,
`PUT /posts/{uid}/save` (an upsert, so moving groups is the same call) and `DELETE /posts/{uid}/save`
(idempotent) complete the set, all three 404ing on a post the caller neither follows nor saved.

T6 put the real app on this API. The Nuxt frontend now calls it for everything: a `/login`
screen takes a dev token, `app/plugins/api.ts` attaches the bearer on every request and
redirects to `/login` on a 401, the `feeds` store loads `GET /home`, `usePostList(uid)` pages
`GET /feeds/{uid}/posts`, `usePost(uid)` reads and saves one post, and the `settings` store
round-trips `GET`/`PUT /settings`. The frontend's types are generated from this server's
OpenAPI document (`pnpm types:api` → `app/types/api.d.ts`), so a renamed field breaks the
frontend's typecheck. The mock data files are deleted.

T7 made the app writable. `backend/core/api/feeds.py` serves `POST /feeds`
(`{feed_url, folder_uid?}` — find-or-create the global `Source` with its `type` inferred from
the host, and for a brand-new source **run T3's ingest inline**, because fetching the feed is
what proves it is one; a failure deletes the source row again and answers 422 *"That URL isn't
a feed."*), `PATCH /feeds/{uid}` (name only) and `DELETE /feeds/{uid}` (memberships cascade at
the database level, then the source is deactivated if it lost its last subscriber — kept, so
re-subscribing reactivates it). `backend/core/api/folders.py` — tagged **`home`**, not `feeds` —
serves `POST /folders`, `PATCH /folders/{uid}` (name, members and mutes all optional, so the
folder panel's one Save is one call) and `DELETE /folders/{uid}`, returning the
`unsubscribed_count` the confirm sheet predicted. Both obligations T4 handed over are paid off,
and `PUT /home/order` now reads, validates and writes inside one transaction with
`select_for_update()`. On the frontend every `app/stores/feeds.ts` write action calls the API —
optimistic with rollback, except the two creates, which await the server-minted uid — the add
wizard resolves a pasted feed URL into a candidate, and the edit drawer's copy and routes moved
onto [backend.md](./backend.md)'s vocabulary (folder / feed, no "source" on screen).

T8 made sign-in real. `POST /auth/google` (`auth=None`, like `/health`) trades the id_token
Google's button returns for one of our own bearer tokens, minted by T2's `issue_token` and
labelled with the caller's User-Agent, so the device list [backend.md](./backend.md) § Auth
promises starts collecting rows from here. `backend/core/google_auth.py` is the one module that
touches a third party's crypto: it verifies signature, issuer, audience and expiry with
`google-auth`, requires a verified email, collapses every unusable case into one
`InvalidGoogleCredential`, and refuses outright while `GOOGLE_OAUTH_CLIENT_ID` is unset (see
[backend.md](./backend.md) § Decision log — an unset audience isn't a skipped check, it's no
check at all). Identity resolves in `_user_for_google`: by
`google_sub`, else onto a row with the same verified email **that no Google account has claimed**,
else a new user. The response is the **token alone** — the profile still comes from `/me`. On the
frontend `app/stores/auth.ts` gained `signInWithGoogle(credential)`, which hands its token to the
renamed `signInWithToken`, so there is one path after "set the token"; `/login` renders Google's
button above the dev-token field, and **both ways in ship** — a deliberate reversal of this task's
own plan to delete the dev path (§ Decision log). `GOOGLE_OAUTH_CLIENT_ID` (backend) and
`NUXT_PUBLIC_GOOGLE_CLIENT_ID` (Nuxt) are both optional: without them there is no Google button
and the dev token still signs you in. No client secret exists anywhere — this flow doesn't have
one.

T9 put polling on its own. `backend/feedme/broker.py` is the one module that knows Dramatiq
exists: it calls `django.setup()` (load-bearing for the `dramatiq`/`periodiq` CLIs, a no-op
under `manage.py`), builds a `RedisBroker(url=settings.REDIS_URL)`, and adds periodiq's
`PeriodiqMiddleware` plus a hand-written `DjangoConnections` middleware that closes stale
per-thread database connections around every message — nothing in a worker fires Django's
request-started/finished signals, which normally do that. `backend/core/tasks.py`'s
`poll_source(source_uid)` wraps T3's `ingest_source` with no rewrite (`max_retries=3`, a
2-minute time limit) and returns quietly, no exception, on a uid whose source has since been
deleted or deactivated — Dramatiq's retries cover only what can throw, and a dead feed already
has its own `error_count`/backoff, two error models that deliberately don't overlap.
`poll_due_sources()` is periodiq's cron sweep (`*/5 * * * *`, targeting the ~30-minute
per-source cadence) — it **claims** its batch with a plain `update()` before sending, since
`ingest_source` only pushes `next_fetch_at` out when a poll *finishes*, and without the claim a
five-minute sweep would re-enqueue everything still queued or in flight. `ingest.py`'s write
phase (`_upsert_posts` → `_backfill_source_metadata` → `_record_success`) now runs inside one
`transaction.atomic()`, so a worker killed mid-poll leaves nothing half-written.
`docker-compose.yml` gained `worker` (`dramatiq core.tasks --processes 2 --threads 4`) and
`scheduler` (`periodiq -v core.tasks`), sharing `api`'s image through a new `x-backend` anchor
so the three can't drift apart; both skip the migrate/bootstrap entrypoint and wait on `api`'s
healthcheck instead, since only `api` should touch the schema. `manage.py poll_source`/`poll_due`
survive as the manual override, and `POST /feeds`'s inline fetch (T7) was deliberately left
alone — validating a brand-new subscribe is still a synchronous request, not a queued one.

**Not built.** Everything else: no article extraction and no search columns, and the endpoints
stop at `/health`, `/me`,
`/auth/google`, `/auth/logout`, `/home`, `/home/order`, `/settings`, `/feeds`, `/feeds/{uid}`,
`/feeds/{uid}/posts`, `/folders`, `/folders/{uid}`, `/posts/{uid}` and `/posts/{uid}/save`. The
frontend surfaces that have no endpoint behind them yet say so: the add wizard's search resolves
a pasted feed URL and nothing else — a YouTube handle, a bare subreddit name or a keyword finds
nothing until T11's `/discover` — and `PUT /home/order` has no drag-and-drop UI driving it yet.

## Contract resolutions

The models were built from [backend.md](./backend.md); the frontend types in
`app/assets/types.ts` predate it. Five conflicts, settled here so no task has to rediscover
them. [data-model.md](./data-model.md) carries the same resolutions. **Items 1–3 are applied in
the app as of T6**, and `app/assets/types.ts` is now an alias layer over the generated schema,
so these shapes live on the backend rather than in a hand-written file.

**1. `Post.feed_uid` vs `Post.source`.** The frontend gives every post a `feed_uid`, but
backend posts belong to a global `Source` shared across all users. The post-list serializer
resolves source → *the requesting user's* `Feed` uid. The public contract is unchanged; the
join is backend work. Merged streams make this load-bearing — an `all` response carries posts
from many feeds and each card needs its own `feed_uid`. **Amended in T5:** the field is
**nullable**. A saved post outlives unsubscribing, so a `saved` response can carry a post whose
source the reader no longer has a feed for; it returns `feed_uid: null` rather than being
dropped from the list.

**2. `Post.content` vs `summary` / `article_html`.** The frontend has one `content` field; the
backend deliberately splits what RSS gave us (`summary`) from on-demand extracted article text
(`article_html`). Lists and detail return `summary`; the reader calls `/posts/{uid}/article`
separately. **Applied in T6:** the reader renders `summary`, and — since a summary is arbitrary
third-party HTML — renders it as plain text until T10 (§ Decision log, 2026-09-01).

**3. `feed_url` is not user-editable.** `updateFeed()` in `app/stores/feeds.ts` currently
patched `feed_url`, but that field lives on the shared global `Source` — editing it would
repoint every other subscriber's feed. `PATCH /feeds/{uid}` accepts **name only**. **Applied in
T6:** `updateFeed` takes a name, and the edit panel shows the RSS URL as read-only text rather
than an input — it's what tells two feeds apart, so it stays on screen. The API still *returns*
`feed_url`, so the `Feed` type itself doesn't change.

**4. `UserSettings` scope.** The model gained `scrollbar_style` in T4 — it's an appearance
preference that should follow the account across devices. Desktop panel-affordance state (the
sidebar's now-removed `sidebarSettingsOpen`) was deliberately kept out of this scope: not a
preference worth syncing to another device.

**5. Top-level home order.** `Feed.order` and `Folder.order` are separate integer columns.
`PUT /home/order` writes **one shared 0..n-1 sequence** across both tables, where `Feed.order`
is only meaningful for loose feeds — a feed's position *inside* a folder lives on
`FolderMember.order`.

## Decision log

Decided 2026-08-19 while writing this roadmap. Append here when a choice is made; don't
rewrite past entries. Stack-level decisions live in [backend.md](./backend.md) § Decision log.

- **Vertical slice at T6** over finishing the backend first — the frontend gets wired to real
  data as soon as auth, `/home` and the post list exist. Contract mistakes surface while
  they're cheap; three were already found before a line was written.
- **`django-cors-headers` over a Nuxt dev proxy** — Capacitor is planned, and a native app
  calls from `capacitor://localhost` with no Nuxt dev server in front of it. A proxy solves
  only the web-dev case; solving it in Django covers web, native and production.
- **`pytest` + `pytest-django`** — the frontend's manual verification works because you can
  see the UI. Folder cascades, the polymorphic uid resolver, cursor boundaries and token
  expiry regress silently until data is wrong. Tests land with the task that creates the
  logic, not afterwards.
- **Google OAuth deferred to T8, dev tokens from T2** — `manage.py issue_token <email>` prints
  a working bearer token, so every endpoint is testable without Google Cloud Console setup.
- **The login screen ships in T6 with a dev-token field**, not with OAuth. Route middleware
  needs a real redirect target, and putting the dev token behind the login form exercises the
  whole store → header → 401 → redirect loop for real. T8 swaps the field for Google's button
  and deletes the dev path. — **Half reversed in T8 _(2026-09-03)_:** Google's button was added
  *above* the field, and the dev path stays for now. See the T8 entry below.
- **Clean cutover of mock data in T6** — `app/assets/data.ts` and `app/assets/mock-search.ts`
  are deleted once real data renders. No fallback mode, no flag: a second code path that
  silently drifts from the API shape is worse than needing the backend running.

Decided 2026-08-19 while building T1:

- **One `requirements.txt`, dev tools included** — `pytest` and `ruff` run *inside* the `api`
  container, so they have to be in the image. A `requirements-dev` split waits for a real
  production image to keep lean.
- **Curated ruff rule set** (`E, W, F, I, UP, B, DJ`) over the minimal default — the extra
  families catch bug patterns and Django-specific mistakes, not just layout. Migrations are
  excluded: Django's writer emits double quotes, so formatting them fights `makemigrations`.
- **Python auto-format hook** — a PostToolUse hook runs `ruff check --fix` + `ruff format` on
  every `.py` Claude edits, the twin of the existing `eslint --fix` hook. It runs from the host
  `.venv`, which makes that venv semi-required rather than pure IDE convenience.

Decided 2026-08-23 while building T2:

- **Expired tokens are rejected, not deleted** — deleting a dead token on sight turns a
  replayed token into a database write, which is a free way to make the server do work for an
  unauthenticated caller. The rows are inert; T13's retention job can prune them.
- **`last_used_at` is touched at most once an hour** — the sliding window is 30 days, so an
  hour of staleness can never expire a live token, and every other authenticated request stays
  a single indexed read. A test pins the query count at 1 so a future change can't quietly
  reintroduce a write per request.
- **Only the 422 handler was written, not three** — ninja already answers 401 and 404 as
  `{"detail": string}` (both exceptions subclass `HttpError`, whose default handler emits
  exactly that). Only validation differs, with a list of pydantic dicts. So T2 reshapes that
  one and declares `401: ErrorSchema` on each operation, which is what actually matters: it
  puts the error shape in the OpenAPI schema T6 generates TypeScript from.
- **Endpoints live in `backend/core/api/`, one module per resource** — T4 and T5 add `/home`
  and the post list within two tasks, so the package goes in now rather than growing one file
  and splitting it later. Routers mount at `''` with full paths inside; a `/me` prefix would
  force `@router.get('')` and invite a trailing slash.
- **`Status(204, None)`, not `return 204, None`** — django-ninja 1.6.3 deprecates the tuple
  form. Worth knowing before T5 and T7, which return a lot of explicit status codes.
- **The `api` service got a compose healthcheck** — `/health` is opted out of the guard
  precisely so an unauthenticated prober can use it, and nothing was actually probing it. Uses
  `urllib` rather than `curl`, which `python:3.13-slim` doesn't ship.

Decided 2026-08-25 while building T3:

- **`requests` fetches, feedparser only parses** — `feedparser.parse(url, …)` can do the
  conditional GET itself, but it passes no timeout to urllib, so the only bound on a hung
  server is the process-global `socket.setdefaulttimeout()` — which in the `api` container
  would also apply to sockets opened toward Postgres and Redis. Upstream has already deleted
  those HTTP arguments from `parse()` for feedparser 7 and tells callers to use an HTTP client,
  so `requirements.txt` pins `feedparser<7`. The seam also makes the 304 path testable without
  monkeypatching a third-party module's internals, and `requests` lands anyway at T11 for
  discovery's HTML autodiscovery fetch.
- **`published_parsed` before `updated_parsed`** — YouTube bumps `<updated>` on view-count
  changes, so ordering by `updated` would reshuffle the timeline on every poll. Reading
  `updated_parsed` first also leans on a feedparser fallback that emits a `DeprecationWarning`
  and is slated for removal.
- **`bozo` alone is not a failure; zero entries is** — feedparser sets `bozo` on feeds that are
  merely sloppy, which is most of them, and still recovers their entries. Treating `bozo` as an
  error would back off perfectly usable sources. An empty `entries` list is the real signal that
  what came back isn't a feed (an error page, say).
- **`update_or_create` per entry, not a bulk diff** — it only runs on a non-304 response, so the
  write cost lands on feeds that actually changed. Batching is a T9 concern if it ever shows up
  in a profile; the plain version is obviously correct and the uid survives an update.
- **`last_fetched_at` is not touched on failure** — it means "when data last arrived", so a
  stale timestamp beside a rising `error_count` reads correctly in the admin list.
- **The reset admin action doesn't poll inline** — it clears `next_fetch_at` so `poll_due` picks
  the source up, rather than holding an admin request open for one network call per source.
- **Source metadata is backfilled from the feed when blank** — a source created by hand in admin
  (and, from T7, by subscribing to a bare URL) knows only its `feed_url`; the feed itself carries
  the title, site link and icon. Never overwrites a value that's already set.

Decided 2026-08-25 while building T4:

- **`PUT /home/order` is strict** — a stale client half-applying an order is worse than a
  refusal; the reorder UI doesn't exist yet, so a loud 422 is what will tell the future
  drag-and-drop it sent the wrong shape.
- **`GET /settings` answers from an unsaved instance** rather than `get_or_create` — a read
  shouldn't cause a write, the same rule T2 set with "expired tokens are rejected, not
  deleted". The row appears on the first `PUT`.
- **`PUT /settings` is a full replace, all fields required** — true to the verb, and the Pinia
  store already holds all three values. Known sharp edge: a future fourth setting would reset
  to default if an older client omitted it; T6 generating types from this schema is what keeps
  the two sides in step.
- **`Literal` types over plain `str`**, on the settings values and on `HomeFeedSchema`'s feed
  `type` — ninja rejects an unknown value with a 422 for free, and the OpenAPI schema carries
  the allowed set, so T6's generated TypeScript gets real union types instead of `string`. The
  feed `type` case is sharper still: `app/assets/types.ts` already hand-writes `FeedType` as
  `'youtube' | 'reddit' | 'website'`, and leaving the field as `str` would have made the
  generated type degrade a union the frontend already expresses more precisely than the
  backend did. Both are pinned by a drift-guard test asserting the `Literal`'s values match the
  model's `TextChoices`.
- **The top-level order breaks ties on `(order, uid)`** — `Folder.order` and `Feed.order` are
  separate columns that both default to 0, so a tie across the two tables would otherwise let
  the list flicker between reads.
- **Feed metadata is flattened from `Source` into the feed object** — `Source` is backend-only
  per the vocabulary table, so `type` / `site_url` / `feed_url` / `icon_url` appear as fields on
  the feed and `source_uid` never appears at all.

Decided 2026-08-26 while building T5:

- **Saved lists order by `saved_at`, everything else by `published_at`** — `saved` is a pile you
  built, not a timeline you follow, so a post you saved this morning leads it even if it was
  published in 2019. The cost is that the ordering column is part of what resolving a uid
  decides (`Stream.order_field`) and the cursor pages over whichever one it named.
- **The cursor carries the post's public `uid`, not its pk** — base64 is decodable, so an
  integer pk inside an "opaque" cursor is still a pk on the wire, and the `backend-dev` skill's
  rule is to return the uid and never the pk. `uid` is unique and indexed, so it's a valid
  tiebreak within an identical timestamp.
- **A post is readable and savable only if you subscribe to its source or have already saved
  it** — posts are global rows, so "is it mine" isn't a user FK; it's this rule, and it 404s
  rather than 403s because which of the two it is isn't the caller's business. The *or saved*
  half is what keeps a saved post readable forever after you unsubscribe.
- **The per-caller fields are correlated subqueries, not joins** — `Feed` is unique per
  (user, source) and `SavedPost` per (user, post), so `feed_uid` / `saved_group` / `saved_at`
  each resolve to exactly one row and none of them can multiply the post rows. The join spelling
  (`filter(saves__user=…)` + `annotate(F('saves__…'))`) is the trap: Django's join reuse across
  `filter` and `annotate` on a multi-valued relation isn't the one you'd guess. This is what
  holds the list at 2 queries whatever the page size.
- **No new index in T5** — `Post` already has `(source, -published_at)`, which covers the
  per-source scan the merged streams merge over. Adding the `uid` tiebreak column would fatten
  a 32-char varchar into the index for a case that only fires on identical timestamps, and T13
  caps the table anyway. Revisit when `EXPLAIN` on a real page request shows a sort.

Decided 2026-09-01, outside any task (admin and the OpenAPI schema, no endpoint behaviour):

- **Admin is organised by owner, not by table** — settings, feeds, folders, saved posts and
  sessions are inlines on the user's own page, because the question admin gets asked first is
  "what does this account actually have?". The index keeps only the global tables (`Source`,
  `Post`) and `User`. Until T7's write endpoints exist this *is* the subscribe UI, so the
  ergonomics are worth the config.
- **`get_model_perms` returning empty, not unregistering** — `Folder` and `SavedPost` are
  hidden from the index but stay registered, because Django admin has no nested inlines: a
  folder's members and per-folder mute can only be edited on the folder's own page, and the
  saved pile needs a changelist to link to once it outgrows a form. `UserSettings` is the one
  model unregistered outright — it is one row per account and nothing links to it.
- **Tokens can't be created in admin, only revoked** — the plaintext exists once, at mint time
  in `manage.py issue_token`; the table stores a SHA-256 hash. An add form there would be a
  form that cannot produce a working token, so the inline disables adding and deleting a row
  is the revoke button.
- **Four OpenAPI tags — `home` / `feeds` / `user` / `default`** — grouped by what the caller
  is doing, not by module, so `account.py` and `settings.py` share `user` and the whole posts
  module sits under `feeds` (its list endpoint's uid is polymorphic over all / saved / a saved
  group / a folder / a feed — it is "read a feed", not "read posts"). T7's `POST /feeds` and
  `PATCH /feeds/{uid}` join `feeds` rather than opening a fifth group.
- **Hand-written `operation_id` on every route** — ninja derives one from the module path
  otherwise (`core_api_posts_feed_posts`), and T6 generates the frontend's types from this
  schema, so those names would leak into generated client code. `tests/test_openapi.py` pins
  all of it: every operation lands in exactly one declared tag, and no id is left generated.

Decided 2026-09-01 while building T6 (all frontend):

- **SSR renders the shell, every API call runs in the browser** — the cookie-persisted theme
  still paints server-side with no flash, but the bearer token never reaches the Nuxt server.
  That is also exactly how the planned Capacitor build behaves, so there is one data path, not
  a web one and a native one.
- **Generated types land in `app/types/api.d.ts`; `app/assets/types.ts` survives as an alias
  layer** — `Feed`, `Folder`, `Post`, `FeedType` and the response shapes are one-line aliases
  over `components['schemas']`, so no component's imports changed and the aliases still carry
  the prose that explains each shape. The generated file is committed (typecheck must not need
  Docker) and ignored by ESLint.
- **The account's data loads in `app.vue`'s `onMounted`, not in route middleware** — filling
  the stores from client middleware happens *before* the hydration render, so the client
  disagreed with a server render done on empty stores (the feed page's `<h1>` rendered "Feed"
  server-side and "Dev" client-side). `onMounted` is the first moment that can't happen.
  Signing in loads the same two reads, since the app booted signed-out.
- **Stores capture `useNuxtApp()` at setup, not inside actions** — an action can run past an
  await (sign-in loads the account once `/me` returns) and by then there is no Nuxt context to
  find. This was a real bug: sign-in reported an invalid token while `/me` had answered 200.
- **No shared `useAsyncData` cache for the open post** — the mobile tree and the desktop shell
  swap places at the `lg` breakpoint, and a shared entry got cleared out from under the
  survivor, blanking the desktop detail pane. The host that owns the uid fetches the post and
  passes it down to a presentational `FeedPostView`. Cost: one duplicate `GET /posts/{uid}` on
  a desktop deep-load, avoided with the existing `isDesktopNow()` guard.
- **RSS summaries are rendered as text** — a summary is HTML (Reddit wraps a whole `<table>`
  around every post), and nothing sanitises it, so `v-html` is not an option; `stripHtml`
  parses it inertly and shows the text. The real answer is T10's extracted article text — this
  is the honest interim, not the intended reading experience.
- **An unreachable API is a first-class state** — a failed `GET /home` shows "Can't reach the
  server" + Try again, never the first-run empty state: telling someone they follow nothing is
  worse than telling them the network failed. The failure is swallowed inside the store rather
  than raised, so an API that isn't up leaves the app on its feet instead of on Nuxt's error
  page.
- **Settings persistence picks fields explicitly** — persisting the whole store restored
  `loaded: true` from the cookie, which skipped the `GET` and turned every page load into a
  `PUT`, breaking T4's "a read shouldn't cause a write" rule from the other side.
- **The home `order` is applied as a sort at load, not retained** — the home list renders as
  two blocks (folders, then loose feeds), so the one shared sequence only has to survive as far
  as the sort. Interleaving the two blocks is T7's drag-and-drop, which re-reads `/home` anyway.

Decided 2026-09-01 while building T7:

- **Optimistic writes with rollback, except creates** — the local mutation lands first so Save
  and Delete feel instant, and a failed call restores the previous array (the cascading folder
  delete re-reads `/home` instead, since its effect spans both arrays by a rule the client only
  mirrors). Creates await, because the backend mints every public uid: an optimistic row would
  carry a client-invented uid the server is about to replace, and one you could tap through to a
  404 in the meantime.
- **Subscribing takes a pasted feed URL, and fetching it is the validation** — there is no
  cheaper way to know whether a URL is a feed, and T3's ingest already backfills title, site and
  icon from what comes back. The cost is one synchronous network call on the request, held
  deliberately *outside* the transaction; a failure deletes the source row again, so a typo
  leaves no dead global row. T11's discovery will front this with a resolution step for handles
  and subreddit names.
- **The source type is inferred server-side from the host, not taken from the request** — the
  add wizard's type step is a UI filter, and a client is free to be wrong about it.
- **A source outlives its last subscriber, deactivated** — deleting it would throw away every
  post already fetched and every other reader's saves (`Feed.source` is `PROTECT`, `Post.source`
  is `CASCADE`). Polling stops; re-subscribing reactivates the same row for free.
- **Folder writes are tagged `home`, not `feeds`** — a folder is home-screen structure, read
  only through `GET /home` and ordered by `PUT /home/order`. Sits beside the four-tag decision
  above rather than opening a fifth group.
- **The delete-folder orphan check is two plain queries, not one annotated count** — filtering
  on a multi-valued relation and aggregating over it in the same queryset counts the *filtered*
  join rows, the same join-reuse trap T5's post list documents.
- **Removing a feed from a folder drops its mute** — carried-over mutes are intersected with the
  surviving membership rather than validated against it, so one Save can drop a member and mute
  another. A mute sent *explicitly* for a non-member is still a 422: that's incoherent, not a
  leftover. (Found by a test.)
- **A refused subscribe is surfaced in two places, not one** — the folder-scoped add
  (`/edit/:uid/add/input`) commits straight from the search step, because it already knows its
  destination and never renders the destination step. So the error line lives in both
  `add/SearchStep.vue` and `add/DestinationStep.vue`; with only the latter, a bad URL pasted
  inside a folder failed silently.
- **The error sits above the destination list, not below it** — that panel is `touch-none`
  (vaul owns the gesture), so anything under a long folder list can't be scrolled to on mobile,
  and a failure that can't be read reads as nothing having happened.
- **An `/edit/*` route with nothing to edit never shows an empty panel** — every panel is keyed
  on finding its folder or feed, so a stale link or an unreachable API otherwise left the drawer
  open with nothing to press. Two halves of one rule: the sheet doesn't **open** until the store
  has answered (`edit/Drawer.vue`, and the edit branch of the desktop `ContentOverlay.vue`) —
  account data arrives after hydration, so a cold deep link used to slide an empty sheet up, hold
  it for the length of `GET /home`, then slide it back down still empty — and once the store has
  answered, a uid it doesn't know **redirects home**.

Decided 2026-09-03 while building T8. The two `google-auth` traps this task hit are stack-level
and live in [backend.md](./backend.md) § Decision log instead:

- **Both sign-in paths ship — the dev-token field stays on `/login`.** This **reverses** this
  task's own "Done when" and the T6-era entry above that promised T8 would delete the dev path.
  Google's button is the primary control; the dev token stays beside it as the way to sign in as
  any account without a Google identity for it, which is what `manage.py issue_token` was for from
  T2. **Retiring it is an owned follow-up**, and the natural shape is gating the field on
  `import.meta.dev` — which is exactly why it is deliberately *not* gated today: there is no
  production deploy, and a build-time gate would make the field vanish silently the day there is
  one, rather than as a decision someone made.
- **Linking is by verified email, but only onto an unclaimed row.** Resolution order is
  `google_sub`, then `email__iexact` **if that row's `google_sub` is empty** (attach the sub to
  it), else create. Both halves carry weight. `iexact` because `EmailField` is case-sensitive and
  `normalize_email` only lowercases the domain, so a plain match would miss `Martin@` vs `martin@`
  and create a duplicate account instead of linking the existing one. The unclaimed check because
  an email address can be reassigned (Workspace domains especially) while a `sub` never changes —
  linking onto a row another Google account already claimed would hand the new owner of an address
  the previous owner's feeds and saves. That case answers 401.
- **The response is the token alone, not token + profile.** A nested profile would need a public
  field name (`user`) the vocabulary table doesn't have, and with the dev path staying, a bare
  `{token}` lets both sign-ins converge on one frontend action that sets a token and proves it
  against `/me`. [backend.md](./backend.md)'s catalog row was updated to match.
- **`provider` describes the account, not the session.** Once an account is linked, `/me` reports
  `'google'` even in a session started by pasting a dev token. Telling the two apart would need a
  column on `AuthToken`, which isn't worth one while the dev path is temporary. The field is a
  `Literal['google', 'dev']` now, so the generated TypeScript gets the union (T4's rule).
- **A changed Google email does not rewrite the stored one.** When the `sub` is already known the
  claims' `email` is ignored: a changed address could collide with another row's unique email and
  turn a routine sign-in into a 500. The `sub` is the identity; a stale email is the cheaper wrong.
- **Creating the user catches `IntegrityError` and re-reads**, rather than wrapping the insert in
  `transaction.atomic()`. Two simultaneous first sign-ins can both miss the lookup and both insert
  on a unique column; a transaction would not prevent that, only roll one of them back.
- **The client secret is unused and stored nowhere.** The button returns an id_token verified
  against Google's public keys — a secret is only needed for the authorization-code exchange,
  which is a different flow, and the planned Capacitor native plugin doesn't use one either. It is
  deliberately absent from `.env.example`.
- **Sign-in is excluded from the global 401 handler.** `app/plugins/api.ts` returns early for
  `/auth/google` (keyed off `response.url`, since the hook's `request` is the path as passed,
  before `baseURL`): a rejected credential is not a dead session. Verified in the browser — with a
  live session, a rejected credential throws to the page and leaves the token and the route
  untouched; without the guard both were torn down.
- **Google's button chrome is not ours, and it forced two layout decisions.** Measured in the
  running app: the button's iframe paints an opaque white background and bleeds 10px past the
  requested box on every side, so a dark theme arrives inside a white frame and `shape` has no
  visible effect. The wrapper clips the bleed with `overflow-hidden`, and `theme: 'outline'` is
  used because `filled_black` clipped is a near-invisible dark bar on the page background and
  inverts the app's elevation direction (elevated is *lighter*). The login column also narrowed
  from `max-w-screen-sm` to a new `--container-signin` (29rem), because Google caps the button at
  400px and a wider column left it short of the field below it. A fully custom button is
  impossible for this flow — that would be the OAuth *code* flow, needing a server-side secret
  exchange.
- **FedCM left at its default** — `use_fedcm_for_button` is not passed. The non-FedCM button flow
  still works, and opting in on the one step that has to work first-try is an unforced risk; it
  stays the first debugging lever if the button misbehaves. `use_fedcm_for_prompt` is deprecated
  and ignored. We render a button, not One Tap, so `prompt()` is never called.
- **Noted for production, not built:** `ux_mode: 'popup'` breaks under a
  `Cross-Origin-Opener-Policy: same-origin` header — it needs `same-origin-allow-popups`. No
  deploy exists yet, so nothing sets that header today.

Recorded 2026-08-26 while reviewing T4 (no code changed):

- **`PUT /home/order` validates outside its transaction** — folders, feeds and the nested set
  are read and validated before `transaction.atomic()` is entered, so two devices reordering at
  once can both pass validation. `select_for_update()` inside the transaction would close the
  concurrent-*reorder* case but not a concurrent *subscribe* (no gap locks under READ
  COMMITTED). Left alone deliberately: the drag-and-drop UI that would trigger it doesn't exist
  yet, the failure is cosmetic (a misplaced row, corrected by the next `/home`), and a partial
  fix that reads as complete is worse than a recorded one. **Revisit in T7.** — **Closed in T7
  _(2026-09-01)_:** the read, the validation and the write now happen inside one
  `transaction.atomic()` with `select_for_update()` on the caller's folders and feeds.
  Concurrent reorders serialise; a subscribe landing in between still isn't gap-locked, but
  re-reading inside the transaction makes it fail validation loudly (a uid missing from the
  order) instead of half-applying.
- **Two obligations T4 handed to T7.** `Feed.order` is never normalised for feeds inside
  folders, so a feed removed from a folder arrives at the top level carrying a stale `order`
  (usually 0) — `PATCH`/`DELETE /folders/{uid}` must assign it a fresh position. And
  `FolderMember` has no constraint that `folder.user == feed.user`, so `PATCH /folders/{uid}`'s
  set-members path has to verify every feed uid belongs to the caller. — **Both paid off in T7
  _(2026-09-01)_**, in `core/api/folders.py`: every uid in a membership write is checked against
  the caller's own feeds, and a feed that leaves a folder into no other folder is rehomed to the
  end of the top-level order.

Decided 2026-09-03 while building T9:

- **Two error models that don't overlap.** `ingest_source` never raises, so a dead feed can
  never reach Dramatiq's retries — the source's own `error_count` / `next_fetch_at` backoff *is*
  the retry schedule for feed failures. The actor's `max_retries=3` covers only what can throw: a
  database blip, a bug, a killed worker. A test pins that a dead feed doesn't raise out of the
  actor, precisely so it can't burn a retry.
- **The sweep claims what it enqueues.** `ingest_source` only pushes `next_fetch_at` out when a
  poll *finishes*, so without a claim a five-minute sweep re-enqueues everything still queued or
  in flight. The claimed value is where a successful poll would have landed anyway. If the
  process dies between claim and send, that source waits one interval — the cheap failure.
- **The write phase is one transaction.** Makes "killing the worker mid-poll leaves no partial
  state" literally true rather than merely recoverable. Ingest was already idempotent, so the
  next poll converged either way, but a half-written batch that outlives the process is exactly
  what the acceptance is about. The network call is already finished by then, so no lock is held
  across I/O.
- **Plain `dramatiq[redis]` over `django-dramatiq`.** Two deps and ~25 readable lines of boot,
  rather than a package whose `Task` model/admin view we explicitly don't want (job visibility is
  `docker compose logs -f worker`; a source's real state already lives on the `Source` admin
  page). The price is the ~8-line `DjangoConnections` middleware we write ourselves — load-
  bearing, not optional: the worker is threaded, Django's connections are thread-local, and
  nothing in a worker fires the request-started/finished signals that normally close them.
- **periodiq was checked before it was trusted.** dramatiq released 2.2.1 on 2026-09-02;
  periodiq's last release is 0.14.0 (2026-04-16), before that major line, and it pins no
  dramatiq version. So the first build step was booting the periodiq CLI against dramatiq 2.2.1
  on a throwaway actor — it registers and schedules correctly. Recorded because it is the
  thinnest link in the stack; the fallback if it ever breaks is a `manage.py` loop command in the
  same `scheduler` service, and the surface to replace is two symbols.
- **Worker concurrency is pinned at `--processes 2 --threads 4`.** The default is one process
  per CPU x 8 threads, which would open more Postgres connections than its default
  `max_connections` allows — to poll a handful of sources twice an hour.
- **`worker` and `scheduler` don't run migrations.** `entrypoint: []` drops the shared bootstrap
  and `depends_on: api: service_healthy` is the signal that `api` has already migrated. Only one
  service should own schema changes.
- **periodiq's `skip_delay` proved itself in the live test:** a sweep enqueued while the worker
  was down was skipped as stale on restart rather than running backdated.

## Tasks

### T1 — Foundations: CORS, linting, test harness

**Goal.** Put the three things every later task leans on in place before any endpoint exists.

**Why here.** The browser can't call the API at all without CORS, and retrofitting a test
harness after ten endpoints means writing ten tests at once, badly.

**Depends on:** nothing.

**Build.**

- Add `django-cors-headers` to `requirements.txt` and `INSTALLED_APPS`. Its middleware must sit
  **above** `CommonMiddleware` in the `MIDDLEWARE` list — Django runs middleware top-down, and
  the CORS headers have to be attached before anything else can short-circuit the response.
  Drive the allowed origins from a `CORS_ALLOWED_ORIGINS` env var, seeded with the Nuxt dev
  origin (`http://localhost:3000`).
- Add `ruff` with its config in `backend/pyproject.toml`, set to single quotes to match the
  existing Python style. (Proposed rather than added silently, per the `backend-dev` skill —
  the backend is about to grow well past a few modules.)
- Add `pytest` + `pytest-django`, a `pytest.ini`/`pyproject` section pointing at
  `feedme.settings`, and `backend/conftest.py` with a `user` fixture. An `authed_client`
  fixture gets added in T2 once tokens exist.
- Harden settings: raise on a missing `SECRET_KEY` when `DEBUG` is off, so a misconfigured
  production deploy fails loudly instead of running on the insecure dev key.

**Done when.** `docker compose exec api pytest` is green on one placeholder test,
`docker compose exec api ruff check .` is clean, and a `fetch('http://localhost:8000/api/v1/health')`
from a page on `localhost:3000` succeeds without a CORS error in the console.

> `requirements.txt` changed, so refresh **both** environments: `docker compose build api`
> (what actually runs) and `.venv/bin/pip install -r backend/requirements.txt` (what the IDE
> reads for autocomplete). See [backend.md](./backend.md) § Docker & dev environment.

### T2 — Auth: bearer tokens, global guard, `/me` ✅

**Goal.** Every endpoint requires a valid bearer token, and you can mint one for yourself.

**Why here.** [backend.md](./backend.md) § Auth makes the app login-only with no anonymous
surface. Building endpoints first and bolting the guard on later means re-testing all of them.

**Depends on:** T1 (the test harness).

**Build.**

- `backend/core/auth.py` — mint with `secrets.token_urlsafe(32)`, store **only** the SHA-256
  hash in `AuthToken.token_hash`, return the plaintext once and never again. A database leak
  then leaks no live sessions.
- A django-ninja `HttpBearer` subclass: hash the presented token, look it up, enforce the
  sliding 30-day window, touch `last_used_at`, return the user (ninja puts it on
  `request.auth`). Wire it globally with `NinjaAPI(auth=BearerAuth())`, and opt `/health` out
  with `auth=None` so container healthchecks keep working.
- `POST /auth/logout` (delete the presented token's row — revocation is instant, which is the
  whole reason for opaque tokens over JWT), `GET /me`, `DELETE /me`.
- Typed error bodies via ninja exception handlers: 401 bad/expired token, 404
  not-yours-or-missing, 422 validation.
- `manage.py issue_token <email> [--device-label]`, printing the plaintext token.

**Migration needed.** `AuthToken.last_used_at` is `auto_now_add=True` today, which sets the
value once at creation and never again — sliding expiry cannot work against it. Change to
`default=timezone.now` and touch it explicitly. **Throttle the write**: only save when the
stored value is older than ~1 hour, otherwise every authenticated request costs a database
write.

**Done when.** Every endpoint 401s without a token. A token from `issue_token` authorizes
through ninja's docs UI at `/api/v1/docs` (click Authorize, paste it). Logout revokes
immediately. Tests cover: missing token, malformed token, expired token, the sliding touch,
and revocation.

### T3 — Ingest core (synchronous, no queue yet) ✅

**Goal.** Real posts from real feeds in the database, fetched by a command you run by hand.

**Why here.** T5 builds the post list, and building a post list against an empty table is
guesswork. Doing ingest *before* the queue keeps it a plain function you can call from a test.

**Depends on:** T1.

**Build.**

- Add `feedparser`. It has ~20 years of hardening against malformed RSS — it is the reason
  this backend is Python.
- `backend/core/ingest.py` exposing one plain synchronous function, `ingest_source(source)`:
  conditional GET using the stored `etag` / `last_modified` (feedparser takes both directly),
  early return on a 304, parse entries, upsert Posts by `(source, guid)`, map entry fields onto
  the model, reset `error_count`, set `last_fetched_at` / `next_fetch_at`. Most polls are cheap
  304s — that's what makes polling hundreds of sources affordable.
- Failure path: increment `error_count`, grow `next_fetch_at` exponentially, deactivate the
  source after N consecutive failures. All of it visible and reversible in admin.
- Expose via `manage.py poll_source <source_uid>` and `manage.py poll_due`.

**Why a plain function, not a task.** T9 wraps this in a Dramatiq actor with no rewrite, and
until then it stays callable from tests and the shell without a broker running.

**Dev data.** Create the three real sources from the current mock file in admin — the Medium
Vue tag feed, the YouTube channel, and r/OnePiece, one per source type — plus `Feed` rows
linking them to your superuser, then run `poll_due`. Admin is the tool here; no seed command
is worth writing.

**Done when.** Real posts for all three source types are visible in admin. Tests cover: guid
dedupe on re-poll, the 304 no-op, a malformed feed not raising, and backoff growth on error.

### T4 — `/home` and `/settings` ✅

**Goal.** The app's cold-start round-trip, and account-level preferences.

**Depends on:** T2.

**Build.**

- `GET /home` — one aggregate response: folders (uid, name, ordered `feed_uids`,
  `muted_feed_uids`), feeds (uid, name, type, site_url, feed_url, icon_url), the top-level
  order, and saved counts per group. Prefetch aggressively; this is the request every app
  launch waits on.
- `PUT /home/order` — the shared 0..n-1 sequence across folders and loose feeds (§ Contract
  resolutions, item 5).
- `GET` / `PUT /settings` over `UserSettings`, which gains `scrollbar_style` (migration).

**Done when.** `/home` returns your real feeds, you've checked the query count and it doesn't
grow with the number of feeds, order survives a round-trip, and a test proves a second user's
folders and feeds never appear in the first user's response.

### T5 — Posts: list, detail, save ✅

**Goal.** The polymorphic post list that every reader screen is built on.

**Depends on:** T2 (auth), T3 (data to list).

**Build.**

- `backend/core/postlist.py` owns the uid → queryset resolution, in the frontend's exact
  order: `all` → `saved` → `saved_*` → `folder_*` (members minus muted) → `feed_*`. One module,
  so the order lives in a single place on each side.
- `GET /feeds/{uid}/posts` — newest-first, `?cursor=&limit=` (default 10). The cursor is an
  opaque base64 of `published_at` + id. **Not an offset**: offsets skip or repeat rows when new
  posts arrive mid-scroll, which is exactly what a feed reader does.
- Each post carries the resolved `feed_uid` (§ Contract resolutions, item 1) and `saved_group`
  (null when unsaved), so cards render without a second request.
- `GET /posts/{uid}`, `PUT /posts/{uid}/save` (upsert — moving between groups is the same
  call), `DELETE /posts/{uid}/save`.

**Done when.** Every uid branch returns the right set. A feed muted in a folder is absent from
that folder's stream but still complete on its own page. Paging through a list while inserting
a newer post skips nothing and repeats nothing. Cross-user isolation is tested.

### T6 — Vertical slice: wire the Nuxt app to real data ✅

**Goal.** The real app, on real data, end to end. The checkpoint that proves the contract.

**Why here.** Auth, `/home` and the post list are the minimum that renders the actual product.
Wiring now means the remaining backend tasks are built against a running app instead of a
docs UI.

**Depends on:** T2, T4, T5. This is a frontend session — the backend should be green first.

**Build.**

- `runtimeConfig.public.apiBase` in `nuxt.config.ts`.
- `app/stores/auth.ts` — the token, persisted (the app already runs
  `pinia-plugin-persistedstate`).
- `app/plugins/api.ts` — a `$fetch.create` instance attaching `Authorization: Bearer`, with a
  401 handler that clears the token and redirects to `/login`.
- `app/middleware/auth.global.ts` — guards everything except `/login`.
- `app/pages/login.vue` — minimal: brand, one line, one action. Sign-in is a **dev-token paste
  field** for now. Keep the layout independent of the sign-in control's chrome — Google
  Identity Services constrains how its own button looks, and T8 drops that button in here.
- Generate TypeScript types from `/api/v1/openapi.json` (`openapi-typescript`) and replace the
  hand-written shapes in `app/assets/types.ts`. From here the two sides can't drift. **As
  built:** the generated file is `app/types/api.d.ts` (committed, ESLint-ignored, refreshed
  with `pnpm types:api`) and `app/assets/types.ts` stays as a thin alias layer over it, so
  every component's `import type { Feed } from '~/assets/types'` is unchanged.
- The `feeds` store loads `/home`. Posts leave the store for a `usePostList(uid)` composable
  over `/feeds/{uid}/posts` with infinite scroll — this finally replaces `PostList.vue`'s
  deliberate "show every post for every uid" placeholder.
- Apply contract resolutions 1–3. Delete `app/assets/data.ts` and `app/assets/mock-search.ts`.
- Add the login screen to [screens-and-flows.md](./screens-and-flows.md) — the app is
  login-only by spec and that screen is specced nowhere today.

**Done when.** Signing in with a dev token renders your real subscribed feeds and real fetched
posts, on mobile and desktop. Saving a post survives a reload. `pnpm lint` and `pnpm typecheck`
pass. No import of `assets/data` remains anywhere.

### T7 — Subscribe and folder writes ✅

**Goal.** The add wizard and edit drawer — already built on the frontend — work for real.

**Depends on:** T6.

**Build.** `POST /feeds` (find-or-create the Source from a discovery result or a known
`source_uid`, create the Feed, trigger the initial fetch only when it's the first subscriber),
`PATCH /feeds/{uid}` (name only), `DELETE /feeds/{uid}` (drops folder memberships too),
`POST /folders`, `PATCH /folders/{uid}` (rename / set members / toggle mute),
`DELETE /folders/{uid}`. Deactivate a Source when its last Feed goes — polling stops, the row
stays for a cheap re-subscribe.

The **delete-folder cascade** is API logic, not a database rule: delete the folder and
unsubscribe its members *except* any that also belong to another folder, and return
`unsubscribed_count` for the confirmation dialog.

**From T6.** Every write in the add wizard and edit drawer was store-local going in — the store
actions existed and the UI was finished, so this task is replacing each action's body with a call.
The home list's `order` is applied as a sort at load and not kept, so the drag-and-drop this
task unblocks re-reads `/home` after `PUT /home/order` rather than reconciling locally.

**As built _(2026-09-01)_.** Three things came out differently. `POST /feeds` takes a **pasted
`feed_url`**, not a discovery result or a `source_uid` — discovery doesn't exist until T11 — and
a brand-new Source is fetched **inline**, because that fetch is what validates the URL (§
Decision log). Folder writes are tagged **`home`**, not `feeds`. And the frontend's writes are
optimistic with rollback except the two creates, which await the server-minted uid. Alongside
it, the edit drawer's copy and route segments moved onto [backend.md](./backend.md)'s vocabulary
(`/edit/:uid/feed/:feedUid`), and its three destructive labels are now exactly the ones
[screens-and-flows.md](./screens-and-flows.md) § 7 already specced — "Delete folder", "Delete
feed", "Remove from this folder" — closing the divergence
[current-state.md](./current-state.md) had recorded.

**Done when.** The add wizard and edit drawer flows work against the API, and each cascade rule
in [data-model.md](./data-model.md) § Cascade rules has its own test.

### T8 — Google OAuth ✅

**Goal.** Real sign-in, replacing the dev-token path.

**Depends on:** T2 only. **Pull it forward whenever the Google Cloud Console setup is done** —
nothing else in the roadmap depends on it.

**Build.** `POST /auth/google`: verify the id_token's signature against Google's published keys
with `google-auth`, check audience and expiry, find-or-create the User by Google `sub`, then
issue a token through T2's existing machinery. Frontend: swap the dev-token field on `/login`
for the real Google sign-in and delete the dev path. Includes the Console setup — project,
consent screen, web client id — and `GOOGLE_OAUTH_CLIENT_ID` in `.env`.

**Check first.** Google Identity Services is opinionated about the button that yields an
`id_token` (its own rendered widget or One Tap; a fully custom button generally goes through
the OAuth code flow instead). Confirm the current API with the `librarian` agent before
designing the control.

**From T6.** Settings → Account already reads `/me` — real email, member-since, provider — and
Sign out already revokes the token server-side, so this task only replaces the provider it
reports (`dev` → `google`) and the control that mints the token.

**As built _(2026-09-03)_.** Three things came out differently. **Both sign-in paths ship** —
Google's rendered button sits *above* the dev-token field on `/login` rather than replacing it,
which reverses this entry's own plan and the T6-era decision-log line that promised the deletion;
retiring the dev path is an owned follow-up, not something this task did (§ Decision log for why
it isn't gated on `import.meta.dev` yet). Identity is more than "find-or-create by `sub`": a
verified email links onto an existing row **only when no Google account has claimed it**, and the
collision answers 401. And the endpoint returns the **token alone** — the profile still comes from
`/me`, so both sign-ins share one frontend path. The Console setup produced a web client id only;
`GOOGLE_OAUTH_CLIENT_ID` (backend) and `NUXT_PUBLIC_GOOGLE_CLIENT_ID` (Nuxt) are both optional,
and there is no client secret to store in this flow. The **Check first** question was answered as
suspected: the rendered widget is the only way to an id_token, so `app/pages/login.vue` renders
Google's button and clips its iframe bleed rather than styling it.

**Done when.** Signing in with a real Google account creates the user and lands on the home
screen, and no dev-token path remains on `/login`. — **Amended _(2026-09-03)_:** the second half
was reversed while building; the dev-token field stays for now (see As built). The first half
stands as the acceptance, and `backend/tests/test_google_signin.py` pins the endpoint with 13
tests (172 backend tests green overall).

### T9 — Dramatiq, `worker`, `scheduler` ✅

**Goal.** Polling happens on its own.

**Depends on:** T3.

**Build.** `dramatiq[redis]` + `periodiq`. Wrap T3's `ingest_source` in an actor with retries.
Add a periodiq cron sweep that enqueues sources whose `next_fetch_at` is due, staggered toward
the ~30-minute per-source cadence. Add the `worker` and `scheduler` compose services — same
image as `api`, different command.

**As built _(2026-09-03)_.** Installed `dramatiq[redis]` 2.2.1 and `periodiq` 0.14.0 — no
`django-dramatiq`: its `Task` model/admin view isn't wanted, since job visibility is
`docker compose logs -f worker` and a source's real state already lives on the `Source` admin
page. `feedme/broker.py` is the one module that knows Dramatiq exists as infrastructure —
`django.setup()` first (load-bearing for the CLIs, a no-op under `manage.py`), then the
`RedisBroker`, `PeriodiqMiddleware` and the hand-written `DjangoConnections` middleware. Two
actors in `core/tasks.py`: `poll_source(source_uid)` (`max_retries=3`, 15s–300s backoff, a
2-minute time limit) wraps `ingest_source` unchanged and shrugs off a uid whose source is gone
or deactivated rather than raising; `poll_due_sources()` (`periodic=cron('*/5 * * * *')`,
`max_retries=0`) claims its batch with an `update()` before sending. `ingest.py`'s write phase
is now one `transaction.atomic()`. `docker-compose.yml` restructures `api`/`worker`/`scheduler`
around a shared `x-backend` anchor and adds `worker` (`--processes 2 --threads 4`, pinned below
the default process-per-CPU × 8-threads to avoid opening more Postgres connections than
`max_connections` allows) and `scheduler`, both with `entrypoint: []` and
`depends_on: api: service_healthy`. `manage.py poll_source`/`poll_due` survive as the manual
override, and `POST /feeds`'s inline fetch (T7) was deliberately left alone — validating a
brand-new subscribe is still a synchronous request. Eight decisions are recorded in § Decision log
(2026-09-03, T9). 182 backend tests green (was 172), `ruff check` clean.

**Done when.** Posts appear without anyone running a command, and killing the worker mid-poll
leaves no partial state behind. — **Verified live _(2026-09-03)_:** the scheduler fired
unattended and the worker polled four due sources across its threads in ~1.7s (70 → 129 posts);
a `SIGKILL` sent mid-poll against a deliberately slow feed left the source with zero posts and
`error_count` untouched, and the redelivered message polled cleanly once the broker's heartbeat
window passed; a `SIGTERM` let the in-flight poll finish before shutting down.

### T10 — Article extraction

**Goal.** Reading stays in-app.

**Depends on:** T5.

**Build.** `trafilatura`. `GET /posts/{uid}/article` extracts on first request, caches the
result globally in `article_html` (extracted once, served to everyone), and serves instantly
after. Returns a typed "couldn't extract" signal the reader falls back from — summary plus
Open source. Decide sync-with-timeout vs. queued when you build it; the user is waiting on this
request, which argues for synchronous with a hard timeout.

**Done when.** Opening a post renders extracted article text, a second open is instant
(served from `article_html`), and a page that can't be extracted falls back to summary + Open
source rather than showing an error.

**From T6.** This is what the reader is waiting on. A `summary` is arbitrary third-party HTML
and nothing sanitises it, so the detail view strips it to plain text — Reddit posts arrive
wrapped in a whole `<table>`. Extracted article text is the field the reader is meant to render,
and it is the one that can be rendered as markup.

### T11 — Discovery

**Goal.** The add wizard's search step returns real candidates.

**Depends on:** T7.

**Build.** `GET /discover?type=&q=`. **Website:** a pasted URL → fetch the page → autodiscover
`<link rel="alternate" type="application/rss+xml">`; a keyword searches **our own source
catalog only** (no web-crawl index — that's a Feedly-scale product we're not building).
**YouTube:** a URL or handle resolves cheaply; a keyword hits the Data API — mind the ~10k
units/day quota (≈100 searches), so cache results and prefer the paste path. **Reddit:** a
subreddit URL or name → its `.rss`. Every result carries `already_subscribed`.

Needs `YOUTUBE_API_KEY` and Reddit app credentials in `.env`.

**From T6.** The wizard's search step keeps its real shape — a query in, a loading flag, a
candidate list out. **Since T7** it resolves one case on its own: a pasted **feed** URL becomes a
single candidate, because that is all `POST /feeds` needs. Everything else — a YouTube handle, a
bare subreddit name, a keyword, a site URL that isn't the feed URL — finds nothing until this
endpoint lands. Wiring it is a swap inside `useAddFeedWizard().search()`.

**Done when.** Pasting a blog URL, a YouTube channel URL and a subreddit name each return a
correct candidate in the add wizard, already-subscribed sources are flagged as such, and a
keyword search returns matches from our own catalog.

### T12 — Search

**Goal.** Scoped post search, behind an engine-neutral contract.

**Depends on:** T5.

**Build.** A migration adding the `pg_trgm` extension, `Post.search` as a generated `tsvector`
(title weighted over summary) with a GIN index, and a trigram index on `title` for
partial-word matching that plain FTS misses. `GET /search?q=&scope=&cursor=`, reusing T5's
cursor.

All search SQL lives in `backend/core/search.py` and **nothing else touches the tsvector
column** — that containment is exactly what keeps [backend.md](./backend.md) § Search's
Elasticsearch upgrade path a one-module swap. Frontend: wire the search button that's currently
a TODO on the feed page.

**Done when.** A partial-word search scoped to one feed, to a folder, and to saved each returns
the right posts; muting a feed drops it from that folder's results immediately; and no module
outside `search.py` references the tsvector column.

### T13 — Retention

**Goal.** The posts table and search index stay lean.

**Depends on:** T9.

**Build.** A daily `prune_posts` job deleting unsaved posts past ~90 days and/or beyond the
newest ~500 per source, both tunable. **Saved posts are never pruned.**

**Done when.** On a seeded dataset the job deletes posts past the cutoff, leaves every saved
post untouched regardless of age, and enforces the per-source cap.

## Housekeeping

Non-blocking chores, unowned by any task.

- **Superuser** — set `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` in `.env`, then
  `docker compose restart api`; the entrypoint creates the account. _(Done — both are set.)_
- **After any `requirements.txt` change** — refresh both environments: `docker compose build api`
  and `.venv/bin/pip install -r backend/requirements.txt`. The venv is IDE-only and nothing
  runs from it.
- **`db` / `redis` publish no host ports.** Add a port mapping in `docker-compose.yml` if you
  want to reach Postgres with a host `psql` or a GUI client.
- **Subagent model ids** — the `checker` / `design-reviewer` / `docs` / `git` agents are
  configured with kimi model ids this environment can't reach, so every launch needs a manual
  override. Fix `.claude/agents/*.md` frontmatter (and the model-policy memory) or restore kimi
  access. Unrelated to the backend, but it costs a step on every commit.
