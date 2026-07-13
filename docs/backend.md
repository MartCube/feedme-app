# Backend

The backend spec: what the server does, how it's built, and the API contract the frontend
consumes. Peer to [data-model.md](./data-model.md) (frontend entities) and
[screens-and-flows.md](./screens-and-flows.md) (what the API must serve). Agreed 2026-07-12;
the decision log at the bottom records what was chosen and why.

## Goals & non-goals

**The backend exists to:**

- authenticate users (Google OAuth) and store their personal state: feeds, folders, saved
  posts, settings, home-list order;
- fetch posts from sources (websites, YouTube channels, subreddits) in the background and
  serve them paginated (infinite scroll);
- power the add-wizard's **discovery** (URL or keyword → candidate sources);
- power **post search** scoped to a feed / folder / saved;
- extract **full article text** on demand so reading stays in-app.

**Non-goals (v1):**

- No social surface — users never see each other; no comments, likes, or follower graphs.
- No read/unread tracking — deliberate, fits the anti-engagement philosophy; additive later.
- No public/anonymous endpoints — the app is login-only. Public shareable feed lists are the
  end-game monetization idea; they would be the first anonymous surface, added consciously.
- No recommendations, trending, or popularity signals — ever (see
  [product-overview.md](./product-overview.md)).

## Vocabulary

Agreed naming, used consistently in backend code, API, and these docs:

| Term | What it is | Visible to frontend? |
| --- | --- | --- |
| **Source** | One RSS endpoint (a website/blog, a YouTube channel, a subreddit). Global, deduplicated, polled once no matter how many users follow it. | No — backend-only |
| **Post** | One item of a source. Global, deduped per source by guid. | Yes (uid `post_*`) |
| **Feed** | The user↔source link: *your* handle on a source — custom name, display order. Same noun as the frontend's `Feed` type, deliberately. | Yes (uid `feed_*`) |
| **Folder** | A user's named group of feeds; many-to-many, per-folder mute. | Yes (uid `folder_*`) |
| **Saved** | Per-user post→group map; fixed groups Bookmarks / Favorites / Later. | Yes (uids `saved_*`) |

Merged streams (a folder's read, `all`, `saved`) need no entity name — the polymorphic
`/feeds/{uid}/posts` uid expresses them, mirroring the frontend's resolver order in
[screens-and-flows.md](./screens-and-flows.md).

The **backend mints every public uid** with the prefixes the frontend already resolves:
`feed_*`, `folder_*`, `post_*`, plus the literals `all` / `saved` and the fixed `saved_*`
group uids from `app/utils/saved.ts`. (Mock ids like `art_med_1` are replaced by `post_*`.)

## Architecture: global sources, per-user everything else

The load-bearing decision. Sources and posts are **global and shared**: if 500 users follow
the same subreddit, we store it once and poll it once. Everything user-specific is a thin
layer of small tables on top. Polling cost grows with *distinct sources*, not users — this is
what makes the app scalable and cheap, and it's how Feedly / Miniflux / FreshRSS work.

```
            GLOBAL (fetched by workers, shared by everyone)
   ┌────────────┐ 1     many ┌────────────┐
   │   Source   │────────────│    Post    │
   └────────────┘            └────────────┘
         │ many                    │ many
         │                         │
   ══════╪═════════════════════════╪══════════  per-user layer
         │ many                    │ many
   ┌────────────┐            ┌────────────┐
   │    Feed    │            │ SavedPost  │
   └────────────┘            └────────────┘
     │ many   (custom name,     (group: bookmarks /
     │ many    order)            favorites / later)
   ┌────────────┐
   │   Folder   │──── FolderMember (muted, order)
   └────────────┘
   + User · AuthToken · UserSettings
```

Consequences worth spelling out:

- **Adding a feed** is usually "subscribe to an existing source" — instant, posts already
  fetched. Only the first user to add a source triggers a fetch.
- **Renaming a feed** edits *your* Feed row's name, never the shared Source title.
- A source with **zero remaining feeds** is orphaned: polling stops (it's deactivated, kept
  for cheap re-subscribe; a cleanup job can delete stale orphans later).
- Post content (including extracted article text) is cached **globally** — extracted once,
  served to everyone.

## Stack

**Django 5 + django-ninja + Dramatiq (+ periodiq) + Postgres 16 + Redis**, Docker Compose,
living in `backend/` in this repo (monorepo).

| Piece | Job | Why this one |
| --- | --- | --- |
| Django | ORM, migrations, **admin**, management commands | Admin is the free ops UI a feed aggregator needs daily: inspect sources/fetch errors, flip `active`, revoke tokens — zero UI built |
| django-ninja | The API layer | FastAPI's ergonomics (type-hinted endpoints, Pydantic schemas, auto OpenAPI) inside Django |
| Dramatiq + Redis | Background jobs (polling, extraction, pruning) | Simple, reliable task queue; `periodiq` adds the cron scheduling Dramatiq lacks |
| Postgres | Data **and search** (FTS + trigram) | One store, no sync pipeline — see [Search](#search) |
| feedparser / trafilatura / google-auth | RSS parsing / article extraction / id_token verification | The Python ecosystem is the decisive reason this backend is Python |

The OpenAPI schema ninja generates is the **frontend contract**: TypeScript types for the
Nuxt app are generated from it (e.g. `openapi-typescript`), so the two sides can't drift.

**Rejected alternatives** (recorded so we don't relitigate):

- **FastAPI + SQLAlchemy + Alembic** — same endpoint ergonomics (ninja is FastAPI's design
  ported to Django), but you hand-assemble admin/auth/migrations that Django gives free. Its
  async advantage never activates here: the slow I/O (polling hundreds of RSS endpoints)
  lives in Dramatiq workers, not the web layer, and feedparser/trafilatura are sync anyway.
- **Full-TS monolith (Nitro server routes + Drizzle + BullMQ)** — the blank-slate runner-up:
  one language, natively shared types, one deploy. Loses on parsing-library maturity
  (feedparser has ~20 years of hardening against malformed RSS; trafilatura is
  state-of-the-art extraction — and handling broken feeds *is* the product's core loop) and
  on having no admin.
- **Go** — what Miniflux is built in (worth reading as prior art); great pollers, but low
  CRUD velocity for a solo dev and no admin. **Rails / Elixir** — no reason to leave Python
  given where the parsing libraries live.

## Data model

```
User          google_sub (unique), email, created_at
AuthToken     user FK, token_hash (SHA-256, unique), created_at, last_used_at, device_label
Source        uid, type (website|youtube|reddit), feed_url (unique), site_url, title,
              icon_url, active, etag, last_modified, last_fetched_at, next_fetch_at,
              error_count
Post          uid (post_*), source FK, guid (unique per source), title, post_url, image_url,
              summary, article_html (nullable — filled by on-demand extraction),
              published_at, search (generated tsvector, GIN-indexed) + trigram index on title
Feed          uid (feed_*), user FK, source FK, name (user's custom title), order
              — unique (user, source)
Folder        uid (folder_*), user FK, name, order
FolderMember  folder FK, feed FK, muted (bool), order — unique (folder, feed)
SavedPost     user FK, post FK, group (bookmarks|favorites|later), saved_at
              — unique (user, post): a post lives in exactly one group
UserSettings  user 1:1, theme, feed_list_style, … (grows with Appearance options)
```

**Cascade rules** are exactly [data-model.md](./data-model.md#cascade-rules)'s, enforced
server-side: remove-from-folder unlinks one membership; delete feed removes it from every
folder; delete folder also deletes member feeds *except* those that are in another folder
(the API returns how many were unsubscribed, for the confirmation dialog).

**Retention:** a daily job prunes unsaved posts older than ~90 days (and/or beyond the newest
~500 per source — both tunable). Saved posts are **always kept**. Keeps the table and the
search index lean; a reader is about recent content.

## API

Conventions:

- All endpoints under **`/api/v1`**, JSON, typed ninja schemas.
- **Global auth guard** — every endpoint requires `Authorization: Bearer <token>`; the app is
  login-only, there is no anonymous surface.
- **Cursor pagination** for post lists (opaque cursor encoding `published_at` + id — stable
  under new inserts, unlike offsets), `?cursor=&limit=` (default 10, for infinite scroll).
- Errors: conventional statuses (401 bad/expired token, 404 not-yours-or-missing, 422
  validation) with a typed error body.

### Endpoint catalog

| Method & path | Purpose |
| --- | --- |
| `POST /auth/google` | Body: Google `id_token`. Verify signature → find-or-create User → issue opaque bearer token. Returns token + profile |
| `POST /auth/logout` | Revoke the presented token (delete its row) |
| `GET /me` | Profile: email, member-since, sign-in provider (Settings → Account) |
| `DELETE /me` | Delete account + all user data (tokens, feeds, folders, saved, settings) |
| `GET /home` | **One aggregate round-trip for the home screen:** folders (with member uids + muted uids), feeds (uid, name, type, site_url, icon), top-level order, saved counts per group |
| `PUT /home/order` | Persist home-list reorder: ordered list of top-level uids (folders + loose feeds) |
| `POST /feeds` | Subscribe: a discovery result (or known `source_uid`) + optional destination `folder_uid`. Find-or-create the Source, create the Feed, first subscriber triggers the initial fetch |
| `PATCH /feeds/{uid}` | Rename (the user's Feed row, never the shared Source) |
| `DELETE /feeds/{uid}` | Unsubscribe everywhere (drops folder memberships too) |
| `POST /folders` | Create: name + optional member `feed_uids` |
| `PATCH /folders/{uid}` | Rename / set members / toggle per-folder mute |
| `DELETE /folders/{uid}` | Cascade delete per the rules above; returns `unsubscribed_count` |
| `GET /feeds/{uid}/posts` | **The post list, polymorphic uid:** `all` \| `saved` \| `saved_*` \| `folder_*` (members minus muted) \| `feed_*` — same resolution order as the frontend's `usePostList`. Newest-first, cursor-paginated |
| `GET /posts/{uid}` | Post detail (what RSS gave us) |
| `GET /posts/{uid}/article` | Full article: extract-on-first-request (trafilatura), cached globally in `article_html`, served instantly after. Returns extracted HTML or a "couldn't extract" signal (frontend falls back to summary + Open source) |
| `PUT /posts/{uid}/save` | Body: `{group}` (bookmarks \| favorites \| later). Upsert — moving groups is the same call |
| `DELETE /posts/{uid}/save` | Unsave |
| `GET /discover` | `?type=website|youtube|reddit&q=<url or keyword>` → candidate sources (title, site_url, feed_url, icon, `already_subscribed`). Backs the add wizard |
| `GET /search` | `?q=&scope=<all|saved|saved_*|folder_*|feed_*>&cursor=` — engine-neutral contract, see [Search](#search) |
| `GET /settings` · `PUT /settings` | The persisted `UserSettings` (theme, feed-list style, …) — replaces cookie-only persistence so settings follow the account across devices |

## Auth

**Google OAuth only in v1** (allauth makes adding providers trivial; Apple becomes relevant
when the iOS app ships). The app is **login-only** — no guest mode.

Flow:

1. Frontend obtains a Google **id_token** — Google Identity Services on web, the native
   Google Sign-In plugin under Capacitor. Google's UI does the heavy lifting.
2. `POST /auth/google` with the id_token. Backend verifies the signature against Google's
   published keys (`google-auth`), checks audience/expiry, then finds-or-creates the User by
   Google `sub`.
3. Backend issues an **opaque bearer token**: 32+ random bytes, stored **SHA-256-hashed**
   (a DB leak leaks no live sessions), **sliding 30-day expiry** (touched on use). The
   frontend stores it (cookie/localStorage on web, secure storage on native) and sends
   `Authorization: Bearer …` on every call.

Why opaque and not JWT sessions: a JWT can't be revoked before expiry, so real logout forces
short expiries + refresh tokens + rotation + interceptor logic on both platforms — and the
refresh token ends up in the DB anyway. JWT earns its keep when a verifier *can't* reach your
database (microservices, third parties); here the verifier and the database are the same
process. Opaque gives instant revocation, a device list for Settings → Account for free, and
one indexed sub-millisecond lookup per request. JWT still appears where it belongs: the
Google id_token we *consume* at login is one.

## Fetching pipeline

Per source type — everything is RSS under the hood:

- **Website / blog** — `feedparser` on the source's `feed_url`. Discovery: paste a URL → we
  fetch the page and autodiscover `<link rel="alternate" type="application/rss+xml">`;
  keyword search only matches **our own source catalog** in v1 (no web-crawl index — that's
  a Feedly-scale product we're not building).
- **YouTube** — channels expose plain RSS: `youtube.com/feeds/videos.xml?channel_id=…`, so
  **polling needs no API quota**. The Data API is used only for *discovery* (keyword →
  channel; note the default 10k units/day ≈ ~100 searches — cache results, prefer handle/URL
  paste which resolves cheaply).
- **Reddit** — subreddits expose RSS/JSON; polling uses a single registered **app token**
  (rate limits are generous at our scale: ~100 QPM ≫ thousands of subreddits at 30-min
  intervals). Per-user Reddit account connect (the Feedly pattern) stays **deferred** —
  revisit only if app-level limits bite.

**Jobs** (Dramatiq; cron via periodiq):

| Job | Trigger | What it does |
| --- | --- | --- |
| `poll_source` | Sweep every few minutes enqueues sources with `next_fetch_at` due (targets ~30-min per-source cadence, staggered) | Conditional GET (ETag / Last-Modified — most polls are cheap 304s), parse, upsert posts by (source, guid), reset `error_count` |
| `extract_article` | First `GET /posts/{uid}/article` | Fetch the original page, trafilatura-extract, store `article_html` globally |
| `prune_posts` | Daily | Delete unsaved posts past retention (see data model) |
| failure handling | on poll error | Increment `error_count`, back off (grow `next_fetch_at`), deactivate after N consecutive failures — all visible/reversible in admin |

## Search

**Postgres FTS + pg_trgm. No separate search engine in v1** — decided after a detailed
Elasticsearch comparison (see decision log).

The use case is *scoped* search: part of a title, within one feed / folder / saved list.
That never hits FTS's real scale cliff (ranking huge unscoped result sets), and every ES
advantage either doesn't activate on scoped queries or belongs to features FeedMe rejects
(trending, recommendations) or defers (public lists).

Design:

- `Post.search` is a **generated `tsvector`** (title weighted over summary/content) with a
  **GIN index** — updated in the same transaction as the insert, so search is never stale
  and there is no sync pipeline. A **trigram index** on `title` (pg_trgm) covers
  partial-word matching ("rout" → "router"), which plain FTS's whole-word tokens miss.
- Scoping is a `WHERE` clause joining the live Feed/Folder/SavedPost tables — mute a feed
  and search reflects it instantly.
- **The engine is hidden behind the contract.** `GET /search` takes `q` + `scope` + cursor
  and returns posts — no tsquery syntax, no raw rank scores. All search SQL lives in **one
  backend search module**; nothing else touches the tsvector column. The post table stays
  the source of truth — any future index is derivable from it.

**Elasticsearch upgrade path** — not "never", but trigger-based. Move to a dedicated engine
(Meilisearch or ES) when any of these is true:

1. public feed lists ship and need ranked *global* search (the one real ES use case here);
2. typo-tolerance complaints become real;
3. scoped search p95 exceeds ~200 ms at actual data size.

The migration is contained by design: stand up the service, design mappings against real
query logs, add the sync task, backfill via a bulk reindex command (needed for drift repair
anyway), and swap the one search module behind the unchanged endpoint. Frontend: zero lines.

## Docker & dev environment

`docker-compose.yml` at the repo root; backend code in `backend/`:

| Service | Image / role |
| --- | --- |
| `api` | Django + ninja (dev: runserver; prod: gunicorn) |
| `worker` | Dramatiq worker (same image, different command) |
| `scheduler` | periodiq (same image) |
| `db` | Postgres 16 |
| `redis` | Redis (Dramatiq broker) |

The Nuxt dev server keeps running via `pnpm dev` as today, talking to `api` on localhost.
Production topology (reverse proxy, frontend build/hosting) is **deferred** — nothing in
this spec constrains it. Secrets (Google client id/secret, YouTube API key, Reddit app
credentials) live in an env file, never in git.

## Decision log

All decided 2026-07-12 during the backend planning session:

- **Global shared sources** over per-user copies — polling cost scales with distinct
  sources, not users; renames live on the per-user Feed row.
- **`Feed`** as the name of the user↔source entity ("Subscription" rejected as
  enterprise-speak) — backend and frontend share every noun; only `Source` is backend-only.
- **Django + ninja over FastAPI** — same endpoint ergonomics; Django's admin (the ops UI),
  allauth, migrations and commands outweigh async purity that FeedMe's architecture never
  exercises. Blank-slate runner-up was a full-TS Nitro monolith; lost on parsing-library
  maturity + no admin.
- **Monorepo** — `backend/` beside `app/`, compose at root, OpenAPI-generated TS types.
- **Postgres FTS + trigram over Elasticsearch/Meilisearch** — scoped search never needs
  ES's strengths; ES's costs (1–2 GB JVM, sync pipeline, second backup/upgrade surface) hit
  a solo dev from day one. Written upgrade triggers above keep the door open.
- **Google OAuth only, opaque bearer tokens over JWT** — instant revocation, no refresh
  machinery ×2 platforms, device list for free; JWT solves federated verification we don't
  have. Login-only app: global auth guard, no anonymous endpoints.
- **No read/unread tracking in v1** — anti-engagement philosophy; additive later.
- **Full article extraction on-demand** (first open), cached globally — zero wasted fetches
  vs. extracting at ingest.
- **Retention ~90 days / per-source cap** for unsaved posts; saved kept forever.
- **Per-user Reddit connect deferred**; app-token polling suffices at v1 scale.
