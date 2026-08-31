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

**Last completed:** T5 — Posts: list, detail, save _(2026-08-26)_
**Next up:** **T6 — Vertical slice: wire the Nuxt app to real data**
**Roadmap written:** 2026-08-19

| # | Task | State |
| --- | --- | --- |
| T0 | Scaffold, models, admin | ✅ done _(2026-08-07)_ |
| T1 | Foundations — CORS, ruff, pytest | ✅ done _(2026-08-19)_ |
| T2 | Auth — bearer tokens, global guard, `/me` | ✅ done _(2026-08-23)_ |
| T3 | Ingest core (synchronous) | ✅ done _(2026-08-25)_ |
| T4 | `/home` and `/settings` | ✅ done _(2026-08-25)_ |
| T5 | Posts — list, detail, save | ✅ done _(2026-08-26)_ |
| T6 | **Vertical slice — wire the Nuxt app** | ⬜ next |
| T7 | Subscribe and folder writes | ⬜ |
| T8 | Google OAuth | ⬜ (unblocked from T2) |
| T9 | Dramatiq, `worker`, `scheduler` | ⬜ |
| T10 | Article extraction | ⬜ |
| T11 | Discovery | ⬜ |
| T12 | Search | ⬜ |
| T13 | Retention | ⬜ |

## Current state

The stack runs: `docker compose up -d` brings up `api` (:8000), `db` (Postgres 16,
healthchecked) and `redis`. `worker` and `scheduler` don't exist yet — they arrive with T9.

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

**Not built.** Everything else: no background queue (T3's poller is a command you run), no
article extraction and no search columns, and the only endpoints are `/health`, `/me`,
`/auth/logout`, `/home`, `/home/order`, `/settings`, `/feeds/{uid}/posts`, `/posts/{uid}` and
`/posts/{uid}/save`. On the frontend, `nuxt.config.ts` has no `runtimeConfig` and the `feeds`
store still imports `app/assets/data.ts` directly.

## Contract resolutions

The models were built from [backend.md](./backend.md); the frontend types in
`app/assets/types.ts` predate it. Five conflicts, settled here so no task has to rediscover
them. [data-model.md](./data-model.md) carries the same resolutions.

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
separately. `Post.content` is renamed to `summary` in `app/assets/types.ts` during T6.

**3. `feed_url` is not user-editable.** `updateFeed()` in `app/stores/feeds.ts` currently
patches `feed_url`, but that field lives on the shared global `Source` — editing it would
repoint every other subscriber's feed. `PATCH /feeds/{uid}` accepts **name only**, and T6
removes the `feed_url` branch from `updateFeed`. The API still *returns* `feed_url`, so the
`Feed` type itself doesn't change.

**4. `UserSettings` scope.** The model gained `scrollbar_style` in T4 — it's an appearance
preference that should follow the account across devices. `sidebarSettingsOpen` stays
device-local: it's a desktop panel affordance, not a preference worth syncing.

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
  and deletes the dev path.
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

Recorded 2026-08-26 while reviewing T4 (no code changed):

- **`PUT /home/order` validates outside its transaction** — folders, feeds and the nested set
  are read and validated before `transaction.atomic()` is entered, so two devices reordering at
  once can both pass validation. `select_for_update()` inside the transaction would close the
  concurrent-*reorder* case but not a concurrent *subscribe* (no gap locks under READ
  COMMITTED). Left alone deliberately: the drag-and-drop UI that would trigger it doesn't exist
  yet, the failure is cosmetic (a misplaced row, corrected by the next `/home`), and a partial
  fix that reads as complete is worse than a recorded one. **Revisit in T7.**
- **Two obligations T4 handed to T7.** `Feed.order` is never normalised for feeds inside
  folders, so a feed removed from a folder arrives at the top level carrying a stale `order`
  (usually 0) — `PATCH`/`DELETE /folders/{uid}` must assign it a fresh position. And
  `FolderMember` has no constraint that `folder.user == feed.user`, so `PATCH /folders/{uid}`'s
  set-members path has to verify every feed uid belongs to the caller.

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

### T6 — Vertical slice: wire the Nuxt app to real data

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
  hand-written shapes in `app/assets/types.ts`. From here the two sides can't drift.
- The `feeds` store loads `/home`. Posts leave the store for a `usePostList(uid)` composable
  over `/feeds/{uid}/posts` with infinite scroll — this finally replaces `PostList.vue`'s
  deliberate "show every post for every uid" placeholder.
- Apply contract resolutions 1–3. Delete `app/assets/data.ts` and `app/assets/mock-search.ts`.
- Add the login screen to [screens-and-flows.md](./screens-and-flows.md) — the app is
  login-only by spec and that screen is specced nowhere today.

**Done when.** Signing in with a dev token renders your real subscribed feeds and real fetched
posts, on mobile and desktop. Saving a post survives a reload. `pnpm lint` and `pnpm typecheck`
pass. No import of `assets/data` remains anywhere.

### T7 — Subscribe and folder writes

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

**Done when.** The add wizard and edit drawer flows work against the API, and each cascade rule
in [data-model.md](./data-model.md) § Cascade rules has its own test.

### T8 — Google OAuth

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

**Done when.** Signing in with a real Google account creates the user and lands on the home
screen, and Settings → Account shows real values instead of today's hardcoded placeholders.

### T9 — Dramatiq, `worker`, `scheduler`

**Goal.** Polling happens on its own.

**Depends on:** T3.

**Build.** `dramatiq[redis]` + `periodiq`. Wrap T3's `ingest_source` in an actor with retries.
Add a periodiq cron sweep that enqueues sources whose `next_fetch_at` is due, staggered toward
the ~30-minute per-source cadence. Add the `worker` and `scheduler` compose services — same
image as `api`, different command.

**Done when.** Posts appear without anyone running a command, and killing the worker mid-poll
leaves no partial state behind.

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
