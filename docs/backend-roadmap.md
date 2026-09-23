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

**Last completed:** T15a — Images: proxy, post images, card toggle _(2026-09-22, amended
2026-09-23 with the declared-width floor)_, after T11b — Discovery: YouTube keyword search
_(2026-09-11)_
**Next up:** **T14 — Feed preview** _(planned 2026-09-15)_, ungated. **T15b — Images: feed
icons** and **T15c — Images: article images** are both unblocked now the proxy is real, and
independent of each other; **T15d — the bucket** builds on T15a too, and is the one that makes
`image: null` truthful and retires T15a's two stand-in floors; **T15f — the loading
placeholder** is a small frontend task that came out of using T15a for real — build whichever
the frontend needs first. T11c (Reddit app credentials) and T11d (a catalog worth searching)
each wait on something outside the code; T15e waits on a deploy target.
**Roadmap written:** 2026-08-19

**T15 is five tasks from the start _(2026-09-15)_** — one per stage of the images strategy plus
one per consumer: the proxy with post images (a), feed icons (b), article images (c), the bucket
(d), the CDN / paid step (e). Lettered like T11 so each can land alone; T15b and T15c are
independent of each other, T15d builds on T15a, T15e waits on a deploy target. **A sixth
joined them _(2026-09-23)_:** T15f, the loading placeholder — not part of the original strategy
but a gap that only showed up once real images were on screen.

**T11 was split into four _(2026-09-06)_.** As written it was one task carrying website
autodiscovery, the YouTube Data API, Reddit and keyword search — four integrations, two of them
needing accounts nobody had yet. T11a is the part that needs **no external credentials at all**,
and it turned out to be exactly the part § Done when was written around. Sub-lettered rather than
renumbered so the T12/T13 references already scattered through `docs/` don't churn. **T12 was
built ahead of T11a**, which is why it is dated the same day and appears above it in this table's
reading order.

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
| T10 | Article extraction | ✅ done _(2026-09-05)_ |
| T11a | Discovery — paste a URL | ✅ done _(2026-09-06)_ |
| T11b | Discovery — YouTube keyword search | ✅ done _(2026-09-11)_ |
| T11c | Discovery — Reddit keyword search | ⬜ needs Reddit app credentials |
| T11d | Discovery — keyword search over our own catalog | ⬜ needs a catalog worth searching |
| T12 | Search | ✅ done _(2026-09-06)_ |
| T13 | Retention | ✅ done _(2026-09-07)_ |
| T14 | Feed preview — a candidate's latest posts | ⬜ ungated, beside T15a |
| T15a | Images — proxy, post images, card toggle | ✅ done _(2026-09-22)_ |
| T15b | Images — feed icons | ⬜ after T15a |
| T15c | Images — article images | ⬜ after T15a |
| T15d | Images — the bucket (stage 2) | ⬜ after T15a |
| T15e | Images — CDN, then paid (stage 3) | ⬜ needs a deploy target |
| T15f | Images — the loading placeholder | ⬜ ungated, frontend only |

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

T10 put the article behind an endpoint. `GET /posts/{uid}/article` (operation_id
`get_post_article`, on
the existing `feeds`-tagged router) reuses T5's visibility rule, so a post the caller neither
follows nor saved 404s exactly as detail does, and a cache hit is that one query and no network.
`backend/core/extract.py` is shaped after `core/ingest.py` on purpose — constants on top, one
network function (`fetch_page`) a test replaces wholesale, one entry point (`extract_article`)
that never raises. It runs **synchronously with a hard timeout** rather than as a queued job,
reversing [backend.md](./backend.md) § Fetching pipeline's `extract_article` row (§ Decision log).
`extract_html` is the library seam: trafilatura 2.2.0 with `output_format='html'`, links and
images kept and `favor_precision` deliberately off, then `nh3.clean` against our own
tag/attribute allowlist — which makes sanitising a rule we own rather than a property of a third
party's internals, drops a `javascript:` href while keeping the `<a>`, and unwraps trafilatura's
`<html><body>` shell for free. The column carries **three states** where the wire carries two:
`null` (nobody tried), `''` (a page was read and had no article in it), or the article; the API
answers `ok` / `unavailable`, because the reader falls back the same way for both a page we
couldn't reach and one with nothing in it. A failed fetch is **not** cached — it leaves `null`, so
the next open retries — while a page we actually received and couldn't extract from stores `''`
for admin's sake **and is retried too** (amended after T10 — see § Decision log, 2026-09-05, and
its amendment): one empty read is not evidence about the article.
The fetch refuses to be aimed inside our own network: scheme allowlist, `ipaddress.is_global` on
every redirect hop (redirects are followed by hand precisely so each one is checked), a 2MB cap
read with `iter_content`, non-HTML content types refused, and the DNS-rebinding gap recorded
rather than papered over. A YouTube source short-circuits to `unavailable` with no fetch at all.
**The Nuxt reader was wired to it on 2026-09-18** — `usePost` fires it alongside
`GET /posts/{uid}` and `FeedPostView` renders `article_html` as markup, falling back to
`stripHtml(post.summary)` plus Open source when extraction can't produce one; that half of T10's
acceptance is closed (see the task entry). 208 backend tests green (was 182), `ruff check` clean.

T12 made the lists searchable. `Post.search` is a **persisted generated column** — a tsvector of
`title` (weight A) over `summary` (weight B), both built with the `'english'` dictionary
`core/models.py` declares once as `SEARCH_CONFIG` — so Postgres recomputes it in the same
statement that writes the row and search can never be stale. Migration
`core/migrations/0004_post_search.py` runs `TrigramExtension()` **first**, hand-added because
`makemigrations` never emits an extension operation and `gin_trgm_ops` doesn't exist until it
runs; then the field; then two GIN indexes, `post_search_gin` on the vector and `post_title_trgm`
on `OpClass(Upper('title'), name='gin_trgm_ops')`. Adding a persisted generated column rewrites
the table and computes the vector for every existing row, so there was no backfill migration to
write — all 440 dev posts were populated by the migration itself. **Nothing was installed**:
`pg_trgm` is a Postgres extension and `django.contrib.postgres` (now in `INSTALLED_APPS`, which
is what registers the trigram lookups and `OpClass`) ships with Django, so § Housekeeping's
"after any `requirements.txt` change" chore does not apply to this task. `backend/core/search.py`
is the only module that queries the column — one entry point, `search_stream(user, q, scope)`,
returning a `postlist.Stream` — and a **containment test** enforces that rather than a
convention: it scans `backend/core/**/*.py` and fails if anything but `core/search.py`,
`core/models.py` (which declares the column) or `core/migrations/` references
`django.contrib.postgres.search`, because [backend.md](./backend.md) § Search's one-module-swap
promise is only true while that holds. `backend/core/api/search.py` serves
`GET /search?q=&scope=all&cursor=&limit=` (operation_id `search_posts`, on a `feeds`-tagged
router), reusing `PostPageSchema` / `DEFAULT_LIMIT` / `MAX_LIMIT` from `api/posts.py` so the
response is byte-for-byte a post page. Scope is `postlist.resolve_stream` **reused verbatim**, so
the five-way uid order, the 404 on another user's uid and the folder mute rule are one
implementation, not two. One refactor of existing code and no new behaviour with it: the page
window (order, decode cursor, fetch `limit + 1`, encode the next cursor) moved out of
`api/posts.py`'s `feed_posts` into `postlist.page(stream, cursor, limit)`, now shared by the post
list and search. 255 backend tests green at the time (231 before this task, 24 of them new in
`backend/tests/test_search.py`; the step up from T10's 208 was T11a's, built first but documented
after — see § Status). 263 after T11a's own follow-up tests landed. `ruff check .` clean. **The
frontend calls `/search`** — `usePostList(uid, q)` swaps endpoints when a query is set, driven
from a search box on the post list's title row; see the T12 entry's § Done when.

T13 put a ceiling on the posts table. `backend/core/retention.py` is the one place a deletion
rule lives: `RETENTION` (90 days), `PER_SOURCE_CAP` (500) and `BATCH_SIZE` (1000) are module
constants beside `ingest.py`'s `POLL_INTERVAL`, not settings — nothing here differs per
deployment. `prune_posts(days=, cap=, dry_run=)` runs two passes and a post dies if **either**
catches it: unsaved posts published before `age_cutoff()`, then, per source, unsaved posts
outside the newest `cap` — an `exclude(pk__in=…)` against a subquery sliced on
`('-published_at', '-pk')`, which keeps exactly `cap` rows however the source's timestamps tie,
where comparing against a boundary row's timestamp has to choose between over- and
under-pruning. **A saved post is never deleted**, at any age by either rule, and the exemption
is "saved by anyone" — posts are global rows, so an owner-scoped rule would delete one out from
under another account's saved pile; `_unsaved()` is a correlated `~Exists(…)`, per T5's
subqueries-not-joins rule. Deletes run `BATCH_SIZE` pks at a time, and `--dry-run` is the real
run inside a rolled-back transaction rather than a simulation, because the cap pass ranks
whatever the age pass left behind. `prune_expired_tokens()` sweeps `AuthToken` rows past
`core/auth.py`'s `TOKEN_TTL` (imported, not restated), paying off the forward reference T2 left.
Both are daily actors in `core/tasks.py` (`30 3 * * *` and `45 3 * * *`, `max_retries=3`, since a
daily job that loses its run waits a day rather than five minutes), with
`manage.py prune_posts --days --cap --dry-run` as the manual override, the twin of `poll_due`.
**The one change outside the new module is in `ingest.py`:** `_upsert_posts` no longer *creates*
an entry already past `age_cutoff()` — polling an archive feed put straight back everything the
prune had just deleted, so the two jobs would have fought over the same rows every night — while
an entry already in the table is still updated. No endpoint changed. 285 backend tests green
(was 263, 22 of them new in `backend/tests/test_retention.py`), `ruff check .` clean.

T11b made the YouTube card search. A bare name under it is a Data API `search.list`
(`backend/core/youtube.py` — the one module that spends quota, `fetch_search` its one network
call), each hit mapped to the same `videos.xml` candidate a pasted channel resolves to, with the
channel avatar as `icon_url`. The quota shaped it: answers are cached for a day under a hashed,
normalised key, failures are not cached, and the list is capped at five even when YouTube
overshoots `maxResults`. Django's cache is the broker's Redis (`CACHES` in `settings.py`; tests
swap in locmem, and `cache.clear()` is never called against the real one — it is `FLUSHDB`). No
key is a supported state, like `GOOGLE_OAUTH_CLIENT_ID`: a name finds nothing, a URL or
`@handle` still resolves for free. YouTube not answering is a 503, which the wizard shows as an
error rather than "Nothing found". See the task entry.

Hardened alongside, with a test each: `clean_name` is shared by the feed and folder writes and
422s a NUL byte (Postgres refuses it, so it was a 500); a `feed_url` past the column's 500
characters is a 422 rather than a truncated fetch of a different URL; a Subscribe double-tapped
past the exists-check is caught at the unique constraint and answered as the same 422; an ingest
that raises mid-subscribe deletes the new source row; a brand-new source is created already
claimed for one poll interval so the sweep can't enqueue it while the inline fetch runs;
`PATCH /folders/{uid}` is one transaction from the rename down; `DELETE /me` deactivates every
source the account was the last subscriber of; and a cursor with a naive timestamp is a 422.
`postlist.page()` is shared by the post list and search. **316 backend tests green in the tree
as committed**, `ruff check .` clean.

**Not built.** Everything else: keyword discovery outside YouTube (T11c, T11d — gated on
credentials and on a catalog worth searching), T14's preview, every image the app should show
(T15b–e — [images.md](./images.md); T15a shipped post images, so what's left unproxied is
`Source.icon_url` — feed icons, still only the wizard's hotlinked YouTube avatars — and the
pictures inside an article), and the endpoints stop at
`/health`, `/me`, `/auth/google`, `/auth/logout`, `/home`, `/home/order`, `/settings`, `/feeds`,
`/feeds/{uid}`, `/feeds/{uid}/posts`, `/folders`, `/folders/{uid}`, `/posts/{uid}`,
`/posts/{uid}/article`, `/posts/{uid}/save`, `/search` and `/discover`.
`PUT /home/order` still has no drag-and-drop UI driving it. Every served endpoint now has a
frontend caller — `/posts/{uid}/article` was the last one without, wired 2026-09-18.

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
third-party HTML — renders it as plain text (§ Decision log, 2026-09-01). **Wired 2026-09-18:**
`usePost` calls `/posts/{uid}/article` alongside the post, and the reader renders `article_html`
as markup, falling back to the stripped `summary` plus Open source when extraction can't produce
one.

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
  unauthenticated caller. The rows are inert; T13's retention job can prune them. — **Closed in
  T13 _(2026-09-07)_:** `retention.prune_expired_tokens()` sweeps them on a daily schedule,
  importing `TOKEN_TTL` from `core/auth.py` rather than restating 30 days, so the sweep and
  `BearerAuth`'s expiry test cannot drift apart. Every row it deletes already answers 401, so it
  can end no live session — verified against the running API: a backdated token 401'd both before
  and after the sweep while a live one stayed 200 throughout.
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
  is the honest interim, not the intended reading experience. — **Reasoning holds, intended
  experience shipped _(2026-09-18)_:** the reader now renders `article_html` as markup and keeps
  this stripped-text treatment only for the `unavailable` fallback — the summary is still text;
  only the article is markup.
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

Decided 2026-09-05 while building T10:

- **Synchronous with a hard timeout, not a Dramatiq job.** This **reverses**
  [backend.md](./backend.md) § Fetching pipeline's job table, which listed `extract_article` as an
  actor triggered by the first `GET`. The reader is blocked on this request either way; queueing
  it buys a free web thread at the cost of a polling loop, a third state on screen, and no clean
  way to report failure. Extraction happens once per post for every reader, so the slow path is
  rare. Measured live: first call 0.99s, second 0.012s.
- **Three storage states, two wire states.** `article_html` is `null` (nobody tried) / `''` (a
  page was read and had no article in it) / the article. The API answers only `ok` /
  `unavailable`, because the reader falls back the same way — summary plus Open source — for
  "couldn't reach it" and "nothing in it". A distinction nothing acts on isn't worth putting on
  the wire.
- **A failed fetch is not cached; a successful fetch that extracted nothing is.** A timeout or a
  403 leaves `null`, so the next open retries — one timeout is not evidence about the article, and
  a paywall can lift. Only a page we actually received and couldn't extract from stores `''`. The
  cost is that a truly dead URL is refetched on each open of that post: one bounded call on a rare
  path. The alternative was new columns and a migration for a case that resolves itself. —
  **Amended in the tree committed 2026-09-15:** the empty read is retried as well. A 200 with
  nothing in it is what a bot-challenge page or a half-deployed site serves, and the post is one
  row shared by every subscriber, so caching that reading writes the article off for everyone on
  one bad fetch. The `''` is still stored — admin can tell "tried, empty" from "never tried" —
  but `GET /posts/{uid}/article` extracts again whenever the column holds anything short of an
  article. Same cost as above, now on the truly empty page too: one bounded call per open of a
  rare post. Pinned by `test_a_page_with_no_article_is_retried_on_the_next_open`.
- **Sanitised on write with nh3, not trusted on read.** trafilatura's HTML output is already
  reduced — a fixed tag map, no class/id/style/script — but that is a property of a third party's
  internals, not a contract, and the frontend will render this field as markup. `nh3.clean` with
  our own allowlist makes it a rule we own: it drops a `javascript:` href while keeping the `<a>`,
  keeps nh3's default `rel="noopener noreferrer"` on links, and unwraps trafilatura's
  `<html><body>` document shell for free, so no separate lxml pass is needed. nh3 ships cp38-abi3
  manylinux wheels, so `python:3.13-slim` needs no Rust toolchain. A test pins the sanitiser as
  the load-bearing half by monkeypatching trafilatura to emit hostile markup.
- **`favor_precision` is deliberately left off**, as a named constant. It drops borderline blocks,
  and a truncated article reads worse than one carrying a stray heading. Observed cost on the live
  kk.org post: one category link leaks in above the headline. One edit if that gets worse.
- **SSRF: scheme allowlist, per-hop private-address check, and a size cap.** `post_url` comes from
  a feed a user chose, and unlike ingest — which only stores what it parses — this endpoint hands
  the body back to the caller, so a feed pointing at `http://169.254.169.254/` would read a
  metadata service out through our own API. Redirects are followed **by hand**
  (`allow_redirects=False`, max 3) precisely so the check runs on every hop; `ipaddress.is_global`
  is the single test covering private, loopback, link-local, reserved, multicast and CGNAT ranges
  on both v4 and v6; the body is read with `iter_content` and abandoned past 2MB rather than
  trusting `content-length`; non-HTML content types are refused. **Known limit, stated rather than
  papered over:** the check resolves DNS itself and `requests` resolves again, so a rebinding
  attack that answers differently the second time slips through. Closing it needs the connection
  pinned to the vetted address through a custom transport adapter — disproportionate here, and a
  partial fix that reads as complete is worse than a recorded one (the same rule the T4 review
  applied to `PUT /home/order`).
- **YouTube sources short-circuit to `unavailable` with no fetch.** A watch page is a JS shell
  with no article in it; a megabyte per video open to extract nothing is waste, and summary plus
  Open source is the right treatment for a video anyway. Verified live: 0.010s, no outbound
  request.
- **Observed, worth recording: Reddit extracts to nothing today.** r/OnePiece's comments page
  returns an 8.4KB "JS required" interstitial to a datacenter IP — a real 200 with no article — so
  it correctly stores `''` and the reader falls back. Reddit's RSS summary is what carries the
  content for those posts anyway.

Decided 2026-09-06 while building T11a:

- **T11 split into four, sub-lettered.** One task carrying website autodiscovery, the YouTube Data
  API, Reddit and keyword search is four integrations, two gated on accounts nobody had. Splitting
  surfaced the useful fact that **T11a needs no credentials at all** — and that it is exactly what
  the original § Done when was written around, since the YouTube/Reddit *keyword* branches only
  ever appeared in the § Build prose. Sub-lettered rather than renumbered so the T12/T13
  cross-references already in `docs/` don't churn.
- **The guarded fetch moved to `core/fetch.py` rather than being imported from `extract.py`.**
  Discovery reads a feed *or* a page, so it needs a different accept header, content-type
  allowlist and byte cap; once those are arguments the function is no longer "the article page
  fetcher". The move was forced by the parameterisation, not by taste, and it puts the SSRF rule
  in one module named for it instead of leaving the article extractor acting as an HTTP library
  for the rest of `core/`. Verbatim move — the guard is T10's, unchanged.
- **Declared feeds are returned unprobed; guessed and Reddit ones are probed.** Subscribing
  fetches for real and takes the true title from the feed, so the name a candidate carries is
  provisional and confirming each declared link would multiply the wait to improve a label. A
  guessed `/atom.xml` and a `/r/<name>/.rss` get probed because there the probe *is* the
  validation — nothing else separates a real feed from a 404.
- **Walk up the path when a page declares nothing.** A post URL is what is actually in the address
  bar when somebody decides to subscribe, and post pages routinely declare no feed while their
  section index does. Capped at three fetches, nearest first, **always including the site root** —
  the first cut dropped the root and kept date archives, which is backwards. The first fetch is
  tolerant too: a pasted URL that 404s should cost the walk, not the result.
- **The link parser reads the whole document, not just `<head>`.** Correct-by-spec is not
  correct-by-web: YouTube closes `<head>` after ~700 KB of inline script and puts its `<title>`
  and feed link in the body, which made a pasted channel URL find nothing. Scanning everything
  costs 8 ms on a 1.6 MB page, since `HTMLParser` treats script bodies as CDATA.
- **A lone feed is named after the page's `<title>`, several feeds after their link tags.** The
  `title=` attribute is written for machines — css-tricks says "RSS 2.0", YouTube says "RSS" — so
  it loses to the page title when it is only decorating. With several links it wins instead, being
  the only thing separating a site's posts feed from its comments feed. For the same reason the
  wizard captions a row with its **feed URL** rather than its site URL.
- **A query that resolves to nothing is `200 []`, not an error.** "Nothing found" is the honest
  answer to a keyword the catalog doesn't have yet as much as to a URL hosting no feed, and
  neither is a failure the wizard should paint red. Only a request that actually failed sets the
  error line.
- **`type` is read as the wizard's card, not as truth.** It decides how a *bare name* is
  interpreted — `OnePiece` is a subreddit under the Reddit card and nothing under the others — but
  every result is typed by `infer_type(feed_url)`, so a YouTube channel pasted under the Website
  card comes back `youtube`. Same rule `POST /feeds` already applied to a pasted URL.
- **Verification against live sites is part of the task, not a follow-up.** The suite was green at
  231 while a pasted post URL and a pasted YouTube channel URL both resolved to nothing — neither
  shape was in the fixtures, so nothing failed. Both bugs were found by pasting real URLs, and
  both now have tests.

Decided 2026-09-06 while building T12:

- **Recency, not relevance.** Results order by the stream's own column, newest first, which reuses
  T5's cursor unchanged instead of growing a second, rank-keyed encoding beside it. The vector
  still carries the title-over-summary weights, so switching to ranking later is an `order_by`,
  not a migration.
- **Scope resolution is `postlist.resolve_stream`, reused verbatim — there is no second
  implementation.** That one call is where the five-way uid order, the 404 on another user's uid,
  the folder mute rule and the three per-caller annotations all come from. T12's acceptance
  "muting a feed drops it from that folder's results immediately" is therefore satisfied by *not
  writing code*, which is the part worth recording.
- **The stream's own `order_field` is kept**, so searching inside `saved` reads newest-*saved*
  first — like the list it was opened from, consistent with T5's saved-ordering decision.
- **Two match branches, deliberately different jobs.** Full-text (`websearch`) over title and
  summary, stemmed, plus `title__icontains` for the partial words FTS structurally cannot reach —
  `rout` is not a lexeme in `router`. A test pins that the FTS branch *alone* fails that case, so
  the trigram index can't quietly become dead weight.
- **`websearch` over `plain` / `raw`** — it is the one search_type that treats its input as
  something a person typed. An unbalanced quote or a stray `&` comes back empty instead of raising
  out of the request as a 500.
- **`summary` is searched whole-word but never by substring.** It is arbitrary third-party HTML
  (Reddit wraps a whole `<table>` around every post), so `icontains` on it would match markup.
- **Postgres's default parser discards `tag` tokens, so HTML never reaches the vector** — which is
  *why* no HTML-stripping pass exists anywhere in the ingest or search path. Non-obvious,
  load-bearing, and pinned by a test.
- **A blank or whitespace-only `q` is an empty page, not a 422** — "you typed nothing" isn't a
  client error. The scope is still validated, so a bad scope 404s regardless of what was typed.
- **The functional trigram index, and the risk that was actually settled.** Django compiles
  `__icontains` on Postgres to `UPPER("title"::text) LIKE UPPER(%s)`, so a plain
  `GinIndex(fields=['title'], opclasses=['gin_trgm_ops'])` would never be matched by the planner.
  The open question going in was whether `OpClass(Upper('title'), …)` produces the *same*
  expression. It does, for a better reason than expected: `upper()` only accepts `text`, so
  Postgres applies the same implicit varchar→text cast when it parses the index expression, and
  the index is stored as `gin (upper(title::text) gin_trgm_ops)` — identical to the lookup.
  **Verified rather than assumed:** at 200,000 seeded rows (inside a transaction that was rolled
  back, so the dev data was untouched) the default planner chose
  `Bitmap Index Scan on post_title_trgm`; at the dev database's real 440 rows it correctly picks a
  seq scan instead — which is why the check needed seeded rows, and why "it worked on the dev
  data" would have been no evidence at all. The `Cast()` fallback planned for the other outcome
  was not needed.

Decided 2026-09-07 while building T13:

- **Both rules delete; a post dies if either catches it.** The age window handles a slow source
  accumulating over years, the per-source cap handles a firehose publishing a year's worth in a
  week. Neither one alone bounds the table.
- **A saved post is never deleted, and the exemption is "saved by anyone".** Posts are global
  rows, so an owner-scoped rule would delete a post out from under another account's saved pile.
  A test covers exactly that: `other_user`'s save protects a post its own reader never saved.
- **The cap excludes the newest `cap` pks rather than comparing against a boundary row's
  timestamp.** Comparing timestamps forces a choice between over-pruning (`__lte` deletes posts
  tied at the boundary that sit *inside* the cap) and under-pruning (`__lt` keeps the whole tied
  group, so a source always keeps `cap + 1`). An `IN` against a subquery sliced on
  `('-published_at', '-pk')` keeps exactly `cap`, whatever the ties, and the keep set stays in
  Postgres instead of coming back as a list of pks to send straight out again — LIMIT inside IN
  is a MySQL restriction, and this project is Postgres-only, as migration 0004 already assumes.
  Ranking counts saved posts too: a saved post holds its slot, so the cap bounds what polling
  accumulates, not what a reader kept.
- **A dry run is the real thing, rolled back** — `transaction.atomic()` plus
  `transaction.set_rollback(True)`, not a simulation. The cap pass ranks what the *age* pass
  leaves behind, so a simulated preview would have to re-derive that in a second code path that
  can disagree with the first; against the real dev database a naive simulation would have
  claimed more deletions than there were posts. Verified instead: the dry run predicted 51 and
  the real run deleted exactly 51. The cost is one transaction held for the length of a
  deliberate manual command.
- **Batched deletes.** `BATCH_SIZE` pks per `DELETE` — an unbatched `.delete()` collects every pk
  into memory and holds one transaction for the whole run, and the first prune against a table
  nothing has ever pruned is the big one.
- **`max_retries=3`, not `poll_due_sources`' `0`.** That sweep can afford to wait five minutes
  for the next one; a daily job would wait a full day, and the work is idempotent and batched, so
  a retry resumes where the last attempt stopped. `time_limit` is 15 minutes, above Dramatiq's
  10-minute default, for the same first-run reason.
- **Expired tokens are pruned here, closing T2's forward reference** (see the T2 entry above).
  `TOKEN_TTL` is imported from `core/auth.py` so the sweep and `BearerAuth`'s expiry test can't
  drift, and every row it removes already answers 401 — the sweep can end no live session.
- **The loop between polling and pruning, found on real data.** `prune_posts` deleted 49 posts
  from `nuxt.com/blog/rss.xml` — an archive feed serving all 51 of its entries back to 2019 — and
  the scheduler's very next five-minute sweep put all 49 straight back (`ok — 49 new`), with
  fresh uids and empty `article_html` caches. The two jobs would have fought over the same rows
  every night and the table would never have got lean, which is T13's whole goal. So ingest now
  respects retention's line: `_upsert_posts` reads `retention.age_cutoff()` and won't *create* a
  post the prune would delete that night, while still updating an entry already in the table, so
  a saved post that has aged out keeps tracking its source. **Consequence worth stating:**
  subscribing to a dormant feed whose entries are all past the window now yields a valid feed
  with zero posts. `POST /feeds` still succeeds — it only 422s when feedparser finds no entries
  at all, which is checked before the upsert — so there is no false "That URL isn't a feed."
  Confirmed after the fix: a full 200 re-poll of all 51 archive entries created **0 new** posts
  and updated only the 2 inside the window.
- **Not touched, deliberately.** Sources are never deleted — T7's "a source outlives its last
  subscriber, deactivated" still holds, and a test pins that pruning a source's posts leaves the
  source standing. There is no separate `article_html`-only retention rule, and no admin surface:
  job visibility is still `docker compose logs -f worker`, the story T9 settled. In-flight cursors
  survive a prune, since `postlist.decode_cursor` turns a cursor into a keyset predicate over
  values rather than a row lookup.

Decided 2026-09-15 while writing the images strategy (no code; the reasoning lives in
[images.md](./images.md) § Decision log — these are the roadmap consequences):

- **Images are five tasks, staged.** T15a proves the proxy on real URLs with two consumers
  (card, hero) and the card toggle; T15b and T15c add consumers; T15d adds permanence; T15e is
  deploy-time. Each is additive on the last — the wire contract and the components are fixed in
  T15a and never change shape.
- **T15a jumps ahead of T14.** Both are ungated; images are what the reader is missing most,
  and T14's preview will carry `image` for free once `DiscoverPostSchema` resolves the same way.
- **`image_url` and `icon_url` are renamed on the wire, not repurposed** — `image` and `icon` —
  so the generated types find every consumer. The columns keep their names.
- **The card setting is synced.** It is the fourth appearance preference and follows the other
  three: a `UserSettings` column, a `Literal`, the drift guard, a full-replace `PUT`.

Decided 2026-09-18, outside any task (frontend-only, attached to T14):

- **Add wizard state moves onto the URL — type and query, not picks.** A reload of `/add` today
  loses the wizard entirely; the folder-scoped add already puts the *step* on the route
  (`/edit/:uid/add` vs. `/edit/:uid/add/input`), but not the type or the search term. Direction:
  `/add?type=youtube&q=one+piece`, written with `router.replace` (not `push`) exactly like the
  post list's `?q=` ([current-state.md](./current-state.md) → Built → Feed page v1), with the
  step derived from the params; picks and the destination step stay in `useState`. Deferred to
  T14 rather than built now, so the scheme is designed once together with the preview state — a
  tapped candidate should be addressable too. Rejected: leaving it as-is (fine on Capacitor, but
  the developer and desktop users reload, and there's no deep link), and steps as path segments
  (`/add/youtube/destination` — over-built for four steps, and a destination URL means nothing
  without state).

Decided 2026-09-22 while building T15a:

- **`fill-down`, not `fill`.** Measured against a real YouTube `hqdefault.jpg` (480 × 360, a 45px
  letterbox top and bottom), not a fixture: imgproxy's `rs:fill` skips the crop entirely when the
  source is smaller than the requested size and enlarging is off, so the poster came back exactly
  as fetched — bars included, the one thing the centre crop exists to remove. `rs:fill-down`
  shrinks the *requested* size to fit the source instead, so the crop still runs and the aspect
  ratio still comes out 16:9 at whatever size the source allows: 480 × 270 for that poster,
  640 × 360 for a Reddit preview, 960 × 540 for a full-size blog hero. `images.md` § Sizes and
  formats amended in place (the "imgproxy never enlarges" bullet).
- **`IMGPROXY_USER_AGENT` is not needed — settled, not guessed.** `images.md` § Operations left
  this as a question for T15a's real-URL pass to answer. Both `preview.redd.it` and
  `external-preview.redd.it` served imgproxy's default User-Agent a plain 200, so nothing
  Reddit-specific was required; the knob stays undocumented until a real source actually refuses
  the default.
- **Verified against real URLs, not only the suite** — the `backend-dev` rule fetch/parse
  features already follow. A YouTube poster, two Reddit CDN hosts, a Medium CDN image
  (188 × 106, under the 320px floor — the collapse rule fired on a real thumbnail, not a
  contrived one), a `nuxt.com` hero, a plain `http://` source, a dead URL (404 from the proxy)
  and a tampered signature (403) all matched `images.md` § Rendering. **Not yet run:** the
  `verify` screenshot pass across the four screens (feed list in both card styles, the post-page
  hero, mobile and desktop) — it needs a dev token the model can't materialise, so it stays
  outstanding rather than assumed from the code.

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
`feed_url`**, not a discovery result or a `source_uid` — discovery didn't exist until T11a — and
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

### T10 — Article extraction ✅

**Goal.** Reading stays in-app.

**Depends on:** T5.

**Build.** `trafilatura`. `GET /posts/{uid}/article` extracts on first request, caches the
result globally in `article_html` (extracted once, served to everyone), and serves instantly
after. Returns a typed "couldn't extract" signal the reader falls back from — summary plus
Open source. Decide sync-with-timeout vs. queued when you build it; the user is waiting on this
request, which argues for synchronous with a hard timeout.

**As built _(2026-09-05)_.** The question the entry left open was answered as it suspected:
**synchronous with a hard timeout**, not a queued job — which reverses
[backend.md](./backend.md) § Fetching pipeline's `extract_article` job row (§ Decision log, with
seven more). `GET /posts/{uid}/article` (operation_id `get_post_article`) joins the existing
`feeds` router and reuses T5's `_visible_post`, so a post the caller neither follows nor saved
404s exactly as detail does, and a cache hit costs that one query and no network.
`backend/core/extract.py` is shaped after `core/ingest.py` deliberately — constants on top, one
network function (`fetch_page`) tests replace wholesale, one entry point (`extract_article`) that
never raises — with `extract_html(body, url)` as the library seam: trafilatura 2.2.0
(`output_format='html'`, links and images kept, `favor_precision` off as a named constant) then
`nh3.clean` against our own tag/attribute allowlist, because the frontend will render this field
as markup and that guarantee has to be ours. Three things went beyond the plan. The cache is
**asymmetric**: a page we read and couldn't extract from is remembered as `''`, a page that never
arrived stays `null` and is retried on the next open — **later amended so that `''` is retried
too** (§ Decision log, 2026-09-05, amendment); the stored `''` now only tells admin the page was
tried. The fetch is **hardened against SSRF** —
scheme allowlist, `ipaddress.is_global` on every redirect hop (redirects followed by hand for
exactly that), a 2MB cap and an HTML-only content type — since unlike ingest this endpoint hands
the fetched body back to the caller; the DNS-rebinding gap that remains is recorded, not papered
over. And a **YouTube** source answers `unavailable` without fetching anything. 208 backend tests
green (was 182, 26 of them new in `backend/tests/test_article.py`), `ruff check` clean.

**Done when.** Opening a post renders extracted article text, a second open is instant
(served from `article_html`), and a page that can't be extracted falls back to summary + Open
source rather than showing an error. — **Met on the server _(2026-09-05)_, closed on the
frontend _(2026-09-18)_:** the endpoint and the global cache landed first (first call 0.99s,
second 0.012s; an unextractable page answers `unavailable` rather than erroring), and `usePost`
now fires it alongside `GET /posts/{uid}`; `FeedPostView` renders `article_html` as markup,
keeps the stripped summary as the `unavailable` fallback, and adds the Open source action that
fallback names ([current-state.md](./current-state.md) → Built → Post page v1).

**From T6.** This is what the reader is waiting on. A `summary` is arbitrary third-party HTML
and nothing sanitises it, so the detail view strips it to plain text — Reddit posts arrive
wrapped in a whole `<table>`. Extracted article text is the field the reader is meant to render,
and it is the one that can be rendered as markup.

### T11a — Discovery: paste a URL ✅

**Goal.** The add wizard's search step turns a URL somebody pasted into feeds they can subscribe
to. No external accounts.

**Depends on:** T7.

**Build.** `GET /discover?type=&q=`. A pasted URL is fetched once and resolved: it either *is* a
feed, or it is a page that declares one. Every result carries `already_subscribed`. A keyword
finds nothing — that is T11d.

**As built _(2026-09-06)_.** Three modules, in the shape T3 and T10 already established: one
function per module touches the network, so a test replaces exactly one symbol.

`core/fetch.py` is **moved code, not new** — the SSRF-guarded, size-capped, redirect-following
fetch that T10 wrote inside `core/extract.py`, lifted out and parameterised (`accept`, `timeout`,
`max_bytes`, `allowed_types`, `truncate`). The move was forced rather than chosen: discovery reads
a feed *or* a page, so it needs a different accept header, a different content-type allowlist and
a different cap, and once those are arguments the function has stopped being "the article page
fetcher". The guard itself is unchanged and now covers both callers by construction, which is the
point — both hand a fetched body back to whoever asked, and discovery's URL is the more directly
attacker-chosen of the two, since a user types it. `extract.fetch_page` survives as a thin wrapper,
so T10's tests kept patching the same symbol; the 15 that reached past it into the plumbing
(`extract.CHUNK`, `extract.socket`, `MAX_REDIRECTS`) moved to `tests/test_fetch.py` with the code.
`USER_AGENT` moved here too, out of `ingest.py` — an HTTP module has no business importing its
user-agent from the RSS poller.

`core/discover.py` resolves, in the cheapest order that can answer: a **Reddit URL or bare name**
→ `/r/<name>/.rss` directly (`SUBREDDIT` matches Reddit's own naming rule, so `OnePiece`,
`r/OnePiece` and the full URL are one case); a **YouTube `/channel/UC…` URL** → `videos.xml?
channel_id=…` directly, no page fetch; **anything else** → fetch it once, and if `feedparser`
recognises it (`parsed.version`, not entry count — a new blog with an empty feed is still a feed)
answer with the feed's own title/site/icon. Only then is it treated as a page. `feed_links()`
reads every `<link rel="alternate">` a document declares using stdlib `html.parser` — ~20 lines
rather than a dependency, and deliberately not `lxml`, which is only present as a transitive
trafilatura dep and is not a promise to us. Declared feeds are returned **unprobed**: subscribing
fetches for real and overwrites the name from the feed itself, so confirming each one here would
multiply the wait to improve a label. The `/r/…/.rss` and the guessed paths *are* probed, because
there a probe is the only thing separating a real feed from a 404.

Two shapes broke the naive version and both are fixed with tests pinning them:

- **A post URL is what people actually paste**, and a post page routinely declares nothing while
  the section index above it does — `nuxt.com/blog` resolved, `nuxt.com/blog/meet-nuxi` did not.
  `_pages_upward` now walks up the path, nearest first, ending at the site root, capped at
  `MAX_ANCESTORS = 3` fetches; when a level is dropped it is a middle one, never the root, since
  `/blog/2026/01/some-post` has date archives between it and the page that declares the feed. The
  *first* fetch is tolerant too, so a pasted URL that 404s costs the walk rather than the result.
  Only reached when the pasted page came up empty, so the tidy case is still one request.
- **YouTube closes `<head>` after ~700 KB of inline script** and declares its `<title>` and its
  `videos.xml?channel_id=…` link *below* it, in the body — so a parser that stopped at `</head>`
  made a pasted channel URL resolve to nothing. It now reads the whole document, which costs 8 ms
  even on a 1.6 MB page because `HTMLParser` skips script bodies as CDATA. `MAX_BYTES` is 2 MB and
  truncates rather than refusing, since giving up on a big page would lose a feed we can see.

When a page declares nothing anywhere up the walk, `COMMON_PATHS` (`/feed`, `/rss`, `/rss.xml`,
`/atom.xml`, `/index.xml`) are probed against the site root and the first that parses wins — the
static-site-generator case, which is where most "that blog has no feed" complaints come from.
`infer_type` **moved here** from `core/api/feeds.py` (a `core/` module importing from `core/api/`
is backwards) and is re-exported there; every candidate is typed by its own URL, so a YouTube
channel pasted under the Website card still comes back `youtube` rather than being mislabelled.

`core/api/discover.py` is the HTTP shape plus the one thing discovery cannot know, having no user:
`already_subscribed`, resolved in a single query. `DiscoverResultSchema` is field-for-field
`HomeFeedSchema` minus the uid it hasn't earned, plus that flag — which is why
[backend.md](./backend.md) § Endpoint catalog's old `title`/`icon` wording was corrected rather
than implemented; the § Vocabulary table wins. Frontend: `FeedCandidate` stopped being
hand-written and became `Schemas['DiscoverResultSchema']`, `useAddFeedWizard().search()` is async
and calls `/discover` behind a shared `add-search-seq` guard so a slow earlier search cannot
overwrite a newer one's results, and `SearchStep.vue` renders already-subscribed rows dimmed with
a **"Following"** caption that cannot be picked. Its caption is the **feed URL**, not the site
URL: one page can declare several feeds and that is the only thing telling them apart — the same
reasoning that keeps the RSS URL on screen in the edit panel (§ Contract resolutions, 3).

263 backend tests green; T11a contributes `tests/test_discover.py` (28) and `tests/test_fetch.py`
(17 — 15 moved out of `test_article.py` with the code, 2 new). `ruff check` and `pnpm lint` /
`pnpm typecheck` clean.

**Done when.** Pasting a blog URL, a YouTube channel URL and a subreddit name each return a
correct candidate in the add wizard, and already-subscribed sources are flagged as such. — **Met
_(2026-09-06)_**, verified against live sites rather than only the suite, which is what surfaced
both bugs above: `nuxt.com/blog/meet-nuxi` → `Nuxt Blog` at `/blog/rss.xml` (601 ms);
`overreacted.io/a-complete-guide-to-useeffect/` → its atom and rss feeds, both listed;
`github.blog/changelog/` → three feeds kept apart by their link tags; `news.ycombinator.com` →
`Hacker News`; `youtube.com/@SolentoLounge` and `@Fireship` → their `videos.xml` feeds in ~450 ms;
`reddit.com/r/vuejs/` and a bare `webdev` → their `.rss`. `vuejs.org/blog/` correctly returns
nothing — that path 404s and the site declares no feed. The keyword half of the original T11
§ Done when moved to T11d.

**Known limitation, carried into T11c.** Reddit answers **HTTP 429** to repeated unauthenticated
`/r/<name>/.rss` fetches, so the same subreddit resolves on one search and returns nothing on the
next. `probe_feed` cannot tell a throttle from a subreddit that doesn't exist, so the wizard says
"Nothing found" either way. Reddit app credentials are the fix and are already T11c's stated
prerequisite.

### T11b — Discovery: YouTube ✅

**Goal.** Typing a channel name into the YouTube card searches YouTube, the way YouTube does.

**Depends on:** T11a. **Needs `YOUTUBE_API_KEY` in `.env`.**

**Build.** The Data API for the keyword case. Mind the quota: 10k units/day, and `search.list`
costs **100 units a call** (≈100 searches/day), while `channels.list` costs 1 — so cache results
and keep T11a's paste path as the cheap one. Caching needs a real store: Django has **no `CACHES`
setting yet**, so it currently falls back to per-process memory, which won't survive a second
worker. Point it at the `REDIS_URL` compose already runs for Dramatiq (Django 5 ships a Redis
backend, so nothing is installed).

This is the task the user actually wants for YouTube — **people would rather search than paste**.
URL and `@handle` resolution already work in T11a, so this adds keyword search only, and can also
replace T11a's ~800 KB channel-page download with a 1-unit `channels.list?forHandle=` lookup.

**As built _(2026-09-11)_.** Keyword search only, as planned; the `@handle` path was left on the
free channel-page route (a test pins that it never asks the API). `backend/core/youtube.py` is
the one module that spends quota, in the shape T3/T10/T11a set — constants on top
(`MAX_RESULTS` 5, `CACHE_TTL` a day, the quota's own renewal window), `fetch_search` as the one
network call a test replaces, `search_channels` as the entry point. It raises one exception,
`YouTubeUnavailable`, for quota spent / key refused / network down alike, and
`core/api/discover.py` turns that into **503 "YouTube search is unavailable right now."** — the
one thing `/discover` does *not* answer `200 []` for, because "nothing found" for a blown quota
would be a lie that is hard to debug a day later. The log line carries only the exception's
class name, since `requests`' message carries the URL and the URL carries the key. Caching is
the plan's, made concrete: the key is a SHA-256 of the whitespace-collapsed, case-folded query
(Django warns about spaces in keys, and a query is spaces), a failure is not cached, and the
result is sliced to `MAX_RESULTS` again after parsing because YouTube was **seen live answering
`maxResults=5` with six**. `CACHES` now points Django at the broker's Redis — the Django 5
backend over the client `dramatiq[redis]` already installs, nothing new in `requirements.txt` —
with one rule written beside it: never `cache.clear()` there, it is `FLUSHDB` and the queues
share the database; `conftest.py` swaps every test onto locmem and clears that instead.
`core/discover.py`'s `_keyword` is where the card decides: a bare name is a channel search under
YouTube only when `youtube.is_configured()`, and nothing under Website or Reddit, which wait for
T11d / T11c unchanged. Each hit becomes the same `videos.xml?channel_id=` candidate a pasted
channel resolves to, so subscribing is the same `POST /feeds` either way, with the channel's
default thumbnail as `icon_url`. Frontend: `SearchStep.vue` leads a YouTube row with that
avatar in a circle (square by nature; a website's `icon_url` is as often a wide banner, so
websites get no avatar yet), and `useAddFeedWizard().search()` shows a failed request's
`detail` — the 503 included — as an error rather than "Nothing found". `.env.example` gained
`YOUTUBE_API_KEY`. 12 tests in `backend/tests/test_youtube.py` against a real `search.list`
body trimmed to the fields read; 316 backend tests green in the tree as committed.

**Done when.** A channel name typed into the YouTube card returns matching channels with their
thumbnails, a repeated search spends no quota, and a missing `YOUTUBE_API_KEY` degrades to T11a's
behaviour rather than erroring — the same rule `GOOGLE_OAUTH_CLIENT_ID` follows. — **Met
_(2026-09-11)_:** all three are pinned by tests, and the overshoot case above came from the live
API rather than a fixture.

### T11c — Discovery: Reddit

**Goal.** Typing into the Reddit card searches subreddits, and stops the throttling.

**Depends on:** T11a. **Needs Reddit app credentials in `.env`.**

**Build.** A registered app (reddit.com/prefs/apps → "script") plus the OAuth2 client-credentials
flow to get a token, then `oauth.reddit.com/subreddits/search`. Authenticating also fixes T11a's
recorded 429 problem, which is the half of this task that matters even before keyword search does:
today a subreddit resolves intermittently.

**Done when.** A keyword returns matching subreddits with their subscriber counts, and resolving
the same subreddit repeatedly stops returning nothing.

### T11d — Discovery: our own catalog

**Goal.** A keyword returns feeds other people here already follow.

**Depends on:** T11a. **Needs a catalog worth searching** — meaningless on a near-empty `Source`
table, which is why it is last.

**Build.** A keyword (anything T11a's `_as_url` doesn't read as a URL) matches `Source` on title,
filtered to the requested type, ranked by **how many users actually follow each one** — a count
of `Feed` rows per `Source`, which is already in the schema. **Our own catalog only, deliberately**
— no web-crawl index, that being a Feedly-scale product we are not building
([backend.md](./backend.md) § Fetching pipeline). Merge with the type-specific branches and dedupe
by `feed_url`; the catalog is free and spends no quota, so it goes first.

Worth reusing rather than reinventing: T12 built real search infrastructure over `Post`. Whether
`Source.title` deserves the same trigram treatment or a plain `icontains` is enough is a decision
for this task, not a foregone one — the table is small and the query is one column.

**Done when.** A keyword search returns matches from our own catalog, popular sources first, and
`SearchStep.vue`'s "Nothing found. Try pasting a link." stops being the answer for a keyword that
somebody here already follows.

### T12 — Search ✅

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

**As built _(2026-09-06)_.** The plan held, and installed nothing to do it: `pg_trgm` is a
Postgres extension and `django.contrib.postgres` ships with Django, so `requirements.txt` is
untouched and § Housekeeping's rebuild-both-environments chore doesn't apply here.
`Post.search` is a **persisted generated column** (`SearchVector('title', weight='A')` +
`SearchVector('summary', weight='B')`, both with the `'english'` `SEARCH_CONFIG` constant
`core/models.py` now declares), so the vector is recomputed in the same statement that writes the
row. Migration `0004_post_search.py` runs `TrigramExtension()` by hand first — `makemigrations`
never emits an extension operation, and `gin_trgm_ops` doesn't exist until it does — then the
field, then `post_search_gin` on the vector and `post_title_trgm` on
`OpClass(Upper('title'), name='gin_trgm_ops')`; adding a persisted generated column rewrites the
table, so all 440 dev posts were populated by the migration itself with no data migration to
write. `core/search.py` holds one entry point, `search_stream(user, q, scope)` → a
`postlist.Stream`, and `core/api/search.py` serves `GET /search?q=&scope=all&cursor=&limit=`
(operation_id `search_posts`, on the `feeds`-tagged router) reusing `PostPageSchema` /
`DEFAULT_LIMIT` / `MAX_LIMIT` from `api/posts.py`, so the response is byte-for-byte a post page
and the frontend needs no new type for it. The containment this entry asks for is **enforced by a
test**, not by convention: it scans `backend/core/**/*.py` and fails if anything but
`core/search.py`, `core/models.py` and `core/migrations/` references
`django.contrib.postgres.search`. One refactor of existing code, no behaviour with it: the page
window — order, decode cursor, fetch `limit + 1`, encode the next cursor — moved out of
`api/posts.py`'s `feed_posts` into `postlist.page(stream, cursor, limit)`, now shared by the post
list and search, and `postlist.py`'s docstring states that reuse as fact instead of
forward-referencing this task. Nine decisions are in § Decision log (2026-09-06, T12), including
recency
over relevance and the planner check behind the functional trigram index. 255 backend tests green
(231 before this task, 24 of them new in `backend/tests/test_search.py`), `ruff check .` clean.

**Done when.** A partial-word search scoped to one feed, to a folder, and to saved each returns
the right posts; muting a feed drops it from that folder's results immediately; and no module
outside `search.py` references the tsvector column. — **Server closed, frontend outstanding
_(2026-09-06)_:** driven against the real dev database, not just the suite. Partial words matched
real content (`ski` → "post time skip", `challeng` → "challenge", `sneak` → "sneaking" via the
stemmer, `pirat` → a post whose *summary* says "pirates"); every scope branch answered correctly
(`all`, a feed, the Dev folder, `saved`, `saved_bookmarks`); muting a folder member through
`PATCH /folders/{uid}` dropped its posts from folder-scoped results **immediately, with no
re-index**, while the same feed stayed complete on its own page (the mute was reverted after); a
105-result query paged at `limit=2` across 53 pages with zero duplicates and order preserved; and
`/api/v1/openapi.json` carries `search_posts` under `feeds` with a `$ref` to the shared
`PostPageSchema`, still exactly four tags. At the time the search button was still a TODO and
`pnpm types:api` was deliberately not run, since regenerating `app/types/api.d.ts` would have
added a `/search` path no code called. — **Frontend closed, in the tree committed 2026-09-15:**
the button beside the title in `FeedPostList.vue` is real — the component the mobile feed page
and the desktop posts pane share, which is the point, since the desktop pane has no navbar and
the mobile-only navbar magnifying glass (now removed) could never have served both. The
presentation question this entry left open was answered as **neither sheet nor dialog**: the
search box swaps in for the title on the same row, the query lives on the route as `?q=`
(300ms debounce, `router.replace` so Back leaves the page rather than walking the term), and
`usePostList(uid, q)` pages `GET /search` with the uid as `scope` — the byte-identical page
shape is what let this be a second URL inside the same composable rather than a second
composable. A result's link carries the query so Back from a post returns to the results; the
desktop shell mirrors it as `readerQuery` on the feeds store so a search survives opening
Settings. `app/types/api.d.ts` is regenerated. See
[current-state.md](./current-state.md) → Built → Feed page v1.

### T13 — Retention ✅

**Goal.** The posts table and search index stay lean.

**Depends on:** T9.

**Build.** A daily `prune_posts` job deleting unsaved posts past ~90 days and/or beyond the
newest ~500 per source, both tunable. **Saved posts are never pruned.**

**As built _(2026-09-07)_.** The plan held; two things went beyond it.
`backend/core/retention.py` is the one place a deletion rule lives, in the shape T3 and T10
established — constants on top (`RETENTION` 90 days, `PER_SOURCE_CAP` 500, `BATCH_SIZE` 1000),
plain synchronous entry points below. They are **module constants, not settings**, exactly like
`ingest.py`'s `POLL_INTERVAL` / `MAX_FAILURES`: `settings.py` holds what differs per deployment
and none of this does, while `--days` / `--cap` make a single run tunable without one.
`prune_posts(days=, cap=, dry_run=)` is two passes over `_unsaved()` — a correlated
`~Exists(SavedPost…)` rather than a join on `Post.saves`, per T5's rule — and returns a
`PruneResult(by_age, by_cap)` frozen dataclass shaped after `ingest.IngestResult`, so the actor
and the command each log one line. `age_cutoff(days=None)` is the single place the age line is
computed. `core/tasks.py` gains two daily actors, `prune_posts` (`cron('30 3 * * *')`,
`time_limit=900_000`) and `prune_expired_tokens` (`cron('45 3 * * *')`), wrapping the plain
functions the way `poll_source` wraps `ingest_source`, and
`manage.py prune_posts --days N --cap N --dry-run` is the manual override, twin of `poll_due.py`.

The two beyond the plan. `prune_expired_tokens()` pays off **T2's forward reference** — it
deletes `AuthToken` rows past `core/auth.py`'s `TOKEN_TTL`, imported rather than restated as 30
days. And **polling had to learn retention's line**: the first live run deleted 49 posts from an
archive feed and the scheduler's next sweep recreated all 49, so `ingest.py`'s `_upsert_posts`
now skips *creating* an entry already past `age_cutoff()` while still updating one that is
already in the table (§ Decision log, where the user-visible consequence is recorded — a dormant
feed whose entries are all past the window subscribes as a valid feed with zero posts). No
endpoint changed. Nine decisions are in § Decision log (2026-09-07, T13). 285 backend tests
green (was 263, 22 of them new in `backend/tests/test_retention.py`, plus an `RSS_ARCHIVE`
fixture in `backend/tests/feeds.py`), `ruff check .` clean.

**Done when.** On a seeded dataset the job deletes posts past the cutoff, leaves every saved
post untouched regardless of age, and enforces the per-source cap. — **Met _(2026-09-07)_**,
driven against the real dev database rather than only the suite. Of its 502 posts over 5
sources, `--dry-run` under the default policy reported 49, while `--days 7 --cap 20 --dry-run`
reported 113 past the window plus 340 past the cap, so each flag demonstrably moves its own
pass. Three real posts were then backdated 200 days and one of them saved: the dry run predicted
51, the real run deleted exactly 51, **the saved 200-day-old post survived** and the two unsaved
ones went. `GET /feeds/all/posts`, `GET /feeds/saved/posts` (which listed the survivor) and
`GET /search?q=impedance` (which found it) all answered correctly afterwards, so the prune left
the search index intact. periodiq registers both new schedules alongside `poll_due_sources`
(confirmed in `docker compose logs scheduler`), and both actors ran end to end over Redis in the
real worker.

### T14 — Feed preview: a candidate's latest posts

**Goal.** Judge a discovered feed before subscribing to it. Tapping a candidate in the add
wizard shows its newest posts — what it publishes and when the last one landed — so "is this
feed alive, and is it about what I think" is answered inside the wizard rather than by
subscribing, reading, and unsubscribing. Pays off the `latest items` half of
[screens-and-flows.md](./screens-and-flows.md) § 4's "not yet built" line.

**Depends on:** T11a. No external credentials — every type is RSS underneath, and YouTube's
`videos.xml` costs no quota.

**Build.** `GET /discover/posts?feed_url=` → the candidate's newest posts, as a bare list like
`/discover`. Backend only; the wizard's presentation is a frontend follow-up that consumes
this contract (regenerate `app/types/api.d.ts` with `pnpm types:api` when it starts) — and is
also the occasion to put the wizard's type and query on the URL as query params (decided
2026-09-18, § Decision log), since a tapped candidate should become addressable at the same time.

*Why this shape.* A candidate has no uid, so `feed_url` — the one field the wizard already keeps
from a `/discover` result — is the key. The path is `/discover/posts`, not `/discover/preview`
or a new noun: it is the twin of `GET /feeds/{uid}/posts` for a feed you don't have yet, and
"posts" is already the word. Operation id `discover_posts`, tag `feeds`, beside `discover`.

*Read-only and live, always.* Nothing is written by previewing — the same rule `/discover`
already states in its docstring. The feed is fetched on every call rather than read from `Post`
when a `Source` for that URL happens to exist: a source with no subscribers stops being polled,
so a database branch needs a staleness rule and a live fallback anyway, which is two paths for
one screen. One bounded network call per tap is the same call `POST /feeds` makes to validate a
subscribe. **No server-side cache in v1** — the wizard can hold a preview in its own state
across back-and-forward, and if the live test shows repeated fetches, `core/youtube.py`'s
`cache.get`/`cache.set` against the Redis `CACHES` is a five-line addition, not a design change.

*Moved and reused, not new.* The whole thing is "discover, one step deeper", so it lives in
`core/discover.py` as `preview_feed(feed_url)` with its HTTP shape in `core/api/discover.py`:

- **Fetch** through `discover.fetch_page` — the SSRF-guarded, 2 MB *truncating* fetch T11a
  already uses. Not `ingest.fetch_feed`: that one carries validators and lets `requests` follow
  redirects unchecked, which is fine for a body that is only ever parsed and stored, and not for
  one handed back to the caller. `feed_url` here is the most directly attacker-chosen URL on the
  API — the wizard's own input box, one hop removed — so it goes through the guard by
  construction. Truncation is the right cap: feeds list newest first, so what a 2 MB archive
  feed loses off the end is exactly what a preview doesn't want.
- **Parse** with the same `feedparser.parse(body, response_headers={'content-location': …})`
  call `_from_feed` makes, and the same test — `parsed.version`, not entry count — for "is this
  a feed". Version absent is *not a feed*; version present with no entries is a real, empty feed
  and answers `200 []`.
- **Map** entries with `ingest.py`'s `_entry_to_post`, made public as `entry_to_post` — a
  rename, no behaviour change. This is the load-bearing reuse: the preview shows **exactly what
  subscribing would store** — the same `(untitled)` fallback, NUL stripping, non-http link skip,
  `media:thumbnail`-then-enclosure image pick and summary cap — so a feed cannot look different
  in the wizard than it does on the home screen a minute later. The precedent is
  `feed_metadata`, made public in T3 for the same reason.
- **One deliberate difference: `published_at` is nullable in the preview.** The list clamps a
  dateless entry to *now* because it must order and retention must be able to reach it. A
  preview that says "posted just now" for a feed that gives no dates would mislead on exactly
  the thing the user opened it to check. How `_entry_to_post` / `_published_at` are split to
  allow that is the builder's call; the constraint is that there stays one mapping, not a
  second one for previews.
- **Order and cut:** newest first by `published_at`, dateless entries last, then the first
  `PREVIEW_LIMIT = 10` — a module constant beside `MAX_RESULTS`, not a `?limit=` parameter.
  Feeds aren't reliably ordered, so the sort is ours.

*Response.* `DiscoverPostSchema`, beside `DiscoverResultSchema`: `PostSchema` minus the three
fields an unstored entry cannot have (`uid`, `feed_uid`, `saved_group`) — `title`, `post_url`,
`image_url`, `summary`, `published_at: datetime | None`. Same names on purpose, so the frontend
renders a preview row with the same vocabulary as a post card. `summary` is the raw feed HTML
`PostSchema.summary` already is, and the frontend already `stripHtml`s it; ten Reddit summaries
is ~150 KB, acceptable for a tap, and a tighter cap is a one-liner if it isn't.

*Errors — a preview that lies is worse than one that fails.* `/discover` answers `200 []` for
everything because "nothing found" is honest whether a site is down or has no feed. For a
preview an empty list *means something* — "this feed is dead" — so unreachable and not-a-feed
must not be spelled that way. `PageUnavailable`, `requests.RequestException` and a body
feedparser doesn't recognise all answer **`422 "Couldn't read that feed."`**, one message, the
split `POST /feeds` already makes with *"That URL isn't a feed."* A missing or malformed
`feed_url` is ninja's own 422. `200 []` is reserved for a feed that parsed and has nothing in it.

*Recorded, not solved here.* **Reddit** answers 429 to repeated unauthenticated `.rss` fetches
(T11a's known limitation), and discovery has usually just probed the same URL, so a subreddit
preview will fail with the 422 above more often than it should until T11c authenticates the
fetch. **Retention** is not applied: a dormant feed previews its old posts and then subscribes
with zero (T13's rule) — showing them is the point, since the date on the newest one is the
answer to "is this alive".

*Tests* replace `discover.fetch_page`, like every discovery test, using the bodies in
`tests/feeds.py`: the newest 10 of a longer feed, in date order, dateless last; the mapping
matches what `ingest_source` stores from the same body (the parity test that pins the reuse);
`RSS_NO_DATE` → `published_at: null`; `RSS_ODD_SCHEMES` → the non-http entries are skipped;
`NOT_A_FEED`, a `PageUnavailable` and a `RequestException` → 422 with the message; a feed with
`version` and no entries → `200 []`; no bearer → 401; a private address is refused (the guard
is `core/fetch.py`'s, already covered — one test that the preview goes through it); and **a row
count on `Source` and `Post` before and after**, so the read-only promise is a test rather than a
docstring. `tests/test_openapi.py` picks the new operation up on its own.

**Done when.** For a candidate of each type — a blog's feed, a YouTube channel's `videos.xml`, a
subreddit's `.rss` — the endpoint returns its newest posts with titles, links and dates, inside
the fetch timeout, and writes nothing. A dead URL and a page that isn't a feed answer 422 with a
message the wizard can show; an empty feed answers `[]`. Verified **against live URLs, not only
the suite** — T11a's rule, since both of its bugs were shapes no fixture had.

### T15a — Images: proxy, post images, card toggle ✅

**Goal.** The first image on screen. Cards and the post page show the post's image through an
image proxy — resized, WebP, signed — and a new *Post cards: Image / Compact* setting picks the
card version. Stage 1 of [images.md](./images.md): nothing is stored; that doc carries the
strategy, the wire contract and the rendering rules, and this entry only says what to build.

**Depends on:** nothing new. No credentials — imgproxy is a container, and the secret is one
we mint.

**Build.**

*Compose.* An `imgproxy` service (`ghcr.io/imgproxy/imgproxy`, pin the current v3 tag — check
it at build time), port 8080. Environment: `IMGPROXY_KEY` and `IMGPROXY_SALT` through compose
interpolation with a dev fallback — `${IMGPROXY_KEY:-<hex>}` — so the fallback is written
**once** and the `x-backend` anchor hands the same two values to `api` (plus
`IMGPROXY_PUBLIC_URL`, default `http://localhost:8080`); `IMGPROXY_MAX_SRC_FILE_SIZE` 10 MB;
`IMGPROXY_DOWNLOAD_TIMEOUT` 10 s; `IMGPROXY_TTL` one year, explicit. Private / loopback /
link-local source addresses stay refused (imgproxy's default — the rule `core/fetch.py` had to
write by hand). `.env.example` documents the three variables. `IMGPROXY_USER_AGENT` only if
verification shows Reddit refusing the default.

*Settings.* `IMGPROXY_KEY`, `IMGPROXY_SALT`, `IMGPROXY_PUBLIC_URL` in `feedme/settings.py`, read
like `YOUTUBE_API_KEY`: an empty key is a supported state in which every `image` is `null`.

*`core/images.py` — the seam.* `WIDTHS = (480, 960, 1440, 1920)`, `DEFAULT_WIDTH = 960`, one
entry point `post_image(url) -> dict | None`: for each width, the path
`/rs:fill:{w}:{h}/g:ce/{base64url(url)}.webp` (height = 16:9 of the width), signed as
base64url(HMAC-SHA256(key, salt + path)) with key and salt decoded from hex, under
`IMGPROXY_PUBLIC_URL`; returns `{'src': <960>, 'srcset': '<480> 480w, …'}`; `None` for a blank
URL or an unset key. The module docstring states the rule from images.md — no other module
builds an image URL — and a **containment test** modelled on `test_search.py`'s scans
`core/**/*.py` and fails if anything but `core/images.py` reads an `IMGPROXY_*` setting.

*API.* `ImageSchema(src, srcset)` in `core/api/posts.py`; `PostSchema.image_url` becomes
`image: ImageSchema | None`, resolved by `@staticmethod resolve_image(obj)` →
`images.post_image(obj.image_url)`. The list, detail and `/search` share `PostPageSchema`, so
the three change together. T14's `DiscoverPostSchema`, when it lands, resolves the same way.

*Card toggle.* `UserSettings.post_card_style` — `TextChoices` `image` / `compact`, default
`image` — migration `0005_usersettings_post_card_style.py`; `SettingsSchema` gains the
`Literal`, `GET` answers the default with no row, `PUT` stays a full replace of all four fields;
`tests/test_settings.py`'s drift guard covers the new pair.

*Frontend.* `pnpm types:api`, then `app/assets/types.ts` exports
`PostImage = NonNullable<Post['image']>`. The `settings` store gains `postCardStyle` beside the
three it syncs (and in the persisted `pick` list); `settings/Appearance.vue` gets a *Post cards*
control shaped like the Feed list one. A new `feed/PostImage.vue` — justified by identical
placeholder / error / too-small logic in two hosts — takes `image`, `sizes`, `eager?`, keeps a
`hidden` ref, and renders the 16:9 `bg-muted` box with the `<img>` or nothing at all: `@error`,
or `@load` with `naturalWidth < 320`, hides it. `PostCard.vue` puts it above the date + title
when the style is `image` and `post.image` is set (`sizes="(min-width: 1024px) 40vw, 100vw"`,
lazy); `PostView.vue` puts it above the `<h1>` (`sizes="(min-width: 1024px) 56rem, 100vw"`,
eager). The desktop posts and post panes render the same components, so nothing else moves.
Any Nuxt UI prop not already used in the repo goes through the `librarian` first.

*Tests* (`tests/test_images.py`, plus the two existing files): `post_image('')` and
`post_image` with no key are `None`; a URL yields four widths, `.webp`, the public base, and a
`src` equal to the 960 entry; changing one character of the path changes the signature; the
containment test; list, detail and search carry `image` as an object or `null`; the setting
round-trips through `GET` / `PUT` and the Literal matches the choices.

**As built _(2026-09-22)_.** The plan held, with one recipe change found under real load. The
path was drafted as `rs:fill:{w}:{h}`; measured against a real YouTube `hqdefault.jpg`, imgproxy's
plain `fill` skips the crop entirely when the source is smaller than the requested size and
enlarging is off, so the poster came back 480 × 360, letterbox and all — the one thing the centre
crop exists to remove. The path is now `rs:fill-down:{w}:{h}/g:ce/…`, which shrinks the
*requested* size to fit the source instead (§ Decision log, 2026-09-22). Everything else shipped
as specced: the `x-imgproxy-secret` compose anchor merged into both `imgproxy` and `x-backend`;
the containment test; `PostSchema.image` on list, detail and `/search`; `UserSettings.post_card_style`
behind the full-replace `PUT /settings`; `feed/PostImage.vue`, above the date + title on
`PostCard.vue` and above the `<h1>` on `PostView.vue` (whose top margin drops from `mt-lg` to
`mt-md` when a hero is present). 328 backend tests green, `ruff check` clean, `pnpm lint` and
`pnpm typecheck` clean.

**Done when.** `pytest`, `ruff`, `pnpm lint` and `pnpm typecheck` are clean — **met**. The
running-imgproxy checks a suite can't prove are met too, against real URLs rather than fixtures:
a YouTube `hqdefault.jpg` → 200 `image/webp` 480 × 270, letterbox gone; `preview.redd.it` and
`external-preview.redd.it` → 200 webp 640 × 360, no User-Agent problem (settles § Operations'
open question — `IMGPROXY_USER_AGENT` isn't needed); a Medium CDN image → 200 at 188 × 106,
under the 320px floor, so the app hides it; a `nuxt.com` hero → 200 webp 960 × 540; an `http://`
source → 200; a dead URL → 404 from the proxy, and the card collapses; a tampered signature →
403. **Not yet met:** the `verify` screenshot pass across the feed list (both card styles), the
post-page hero, and mobile/desktop hasn't run — it needs a dev token the model can't materialise
— so `design-reviewer`'s review of it is still outstanding.

### T15b — Images: feed icons

**Goal.** Every feed has a face. The add wizard's rows show an icon for every type — today only
YouTube's avatars are shown, hotlinked with `referrerpolicy="no-referrer"` as an interim fix for
Google's CDN 429ing foreign-referrer hotlinks (measured 2026-09-18) — with initials when a
source has none; home rows and the card's type cue pick the same icon up when the design says
so.

**Depends on:** T15a (the proxy and `core/images.py`).

**Build.** `images.icon(url) -> str | None` (64 × 64 fill; imgproxy reads ICO and SVG, which is
what favicons are). `HomeFeedSchema.icon_url` and `DiscoverResultSchema.icon_url` become
`icon: str | None` (the rename finds every consumer). A **favicon backfill** for sources that
declare no icon: `core/discover.py` already parses a page's `<link>` tags for feeds — add
`rel="icon"` (largest declared size wins), fall back to `/favicon.ico`, and let
`ingest._backfill_source_metadata` store it under the never-overwrite rule. Frontend: the
wizard rows render `UAvatar` with the feed name as the initials fallback, for every type
(`librarian` for the component's fallback and `src` props first). Optional in the same slice,
if small: store Google's `picture` claim on `User` at sign-in, `Me.avatar` through the same
`images.icon`, an avatar on Settings → Account.

**Done when.** The five dev sources show an icon or initials in the wizard; an ICO and an SVG
favicon both render through the proxy against live sites; the containment test still passes.

### T15c — Images: article images

**Goal.** The pictures inside an extracted article load — over https, at reading width, without
leaking the reader to the article's host.

**Depends on:** T15a. The reader has been wired to `/posts/{uid}/article` since 2026-09-18, so
there's now a consumer to verify against.

**Build.** In `post_article`, rewrite every `<img src>` in the cached `article_html` to a
proxied `rs:fit:1920:0` URL (fit, no crop) **at read time** — never into the column, so a key
rotation can't break every cached article. nh3 already limits `<img>` to `src` / `alt` /
`title`, so the rewrite is a pass over one attribute. A relative `src` was absolutised at
extraction; a `data:` or non-http one is dropped with the tag.

**Done when.** A live article with images (kk.org, a Medium post) renders them through the
proxy; the cached column is byte-for-byte unchanged by a read.

### T15d — Images: the bucket (stage 2)

**Goal.** Permanence. Every post's original is ours from the moment it is polled, so a saved
post keeps its image forever, `image: null` is truthful, and the read path never depends on a
stranger's server.

**Depends on:** T15a. No credentials in dev (MinIO in compose); R2 or S3 keys in prod.

**Build** — planned in its own session; the shape is fixed here. A `minio` service with the
bucket created on start; `boto3` and a thin `core/storage.py`; `Pillow` for a header-only
dimension read; `Post.image_key` (blank when none), `image_width`, `image_height` + migration;
an actor `fetch_source_images(source_uid)` enqueued at the end of `ingest_source` for posts with
an `image_url` and no key, running **sequentially per source** through `core/fetch.py`'s guarded
`fetch_url` with image content types and a 10 MB cap; `images.post_image` builds an `s3://`
source when a key exists and answers `null` below 320px wide; `retention.prune_posts` deletes
the objects of the posts it deletes; `manage.py fetch_images` as the backfill; imgproxy gains
`IMGPROXY_USE_S3`, the endpoint and keys. Open for that plan: the retry policy for a failed
fetch, and whether to store a size-capped master instead of the raw original.

*It also retires two stand-ins* _(added 2026-09-23)_. Real dimensions at ingest are what finally
make `image: null` truthful, so this task deletes both of the things standing in for them today:
`core/images.py`'s `_declared_too_small` (which can only read a `width=` the source happens to
put in its own URL) and `PostImage.vue`'s read-time collapse (which lays the box out and then
removes it — the flicker T15a shipped with). Until then they are a pair: the server drops what it
can prove is too small, the client drops the rest once the bytes arrive.

**Done when.** A freshly polled feed's images appear within a poll; deleting the source's image
on the web changes nothing on screen; pruning a post removes its object; a `--dry-run` of the
backfill reports what a real run would fetch; and no card lays out an image box it then removes.

### T15e — Images: CDN, then paid (stage 3)

**Goal.** Fast first views and a transform budget that grows with money rather than code.

**Depends on:** a deploy target — [backend.md](./backend.md) § Docker defers production
topology, and this task is the first thing that needs a hostname.

**Build.** `img.<domain>` → imgproxy, proxied through Cloudflare's free tier;
`IMGPROXY_PUBLIC_URL` set to match; the one-year `Cache-Control` imgproxy already sends is what
makes the CDN the store for derived images. Later, when transform CPU shows on a graph: a second
imgproxy replica, or a managed transformer reading from the bucket (Cloudflare Images
Transformations, Bunny Optimizer) — a change inside `core/images.py` and nothing else. AVIF via
`<picture>` if bandwidth ever matters.

**Done when.** A second load of any image is a CDN hit; rotating the key invalidates every URL
and the cache refills without a code change.

### T15f — Images: the loading placeholder

**Goal.** Make the reserved box say "an image is coming" instead of sitting there as a flat grey
rectangle. Frontend only, one component.

**Depends on:** T15a, and on the declared-width floor landing with it _(2026-09-23)_ — before
that, a nicer placeholder would only have dressed up the flicker, since four cards in ten laid
out a box for an image that never arrived. With the floor in place the reserved box is honest
in almost every case, which is what makes this worth doing on its own.

**Build.** `feed/PostImage.vue`'s `bg-muted` box is the whole surface area: give it a resting
treatment while the image is in flight and drop it on `@load`. The repo already has the
vocabulary — `USkeleton` is what `PostView.vue` shows while the article loads, so the reader
has seen this animation before. Tokens only, no new dependency, and nothing else in the app
changes. Whether the treatment is that same pulse or something quieter is the design call to
make with the component on screen.

*Not in this task.* A **colour-accurate** placeholder — the image's dominant colour, or a
blurhash, behind the box so the card settles into its own palette — needs a value computed from
the bytes at ingest, which is a column and a pass over every post. That rides on T15d, where
the worker already opens each original to read its dimensions, and it is the reason this task
is deliberately small: the cheap version is worth having now and does not block the good one.

**Done when.** A card with a slow image shows a live placeholder rather than a grey block, and
a card whose image is already cached shows no placeholder flash at all. `verify` screenshots,
mobile and desktop, reviewed by `design-reviewer`.

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
