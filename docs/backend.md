# Backend

The backend spec: what the server does, how it's built, and the API contract the frontend
consumes. Peer to [data-model.md](./data-model.md) (frontend entities) and
[screens-and-flows.md](./screens-and-flows.md) (what the API must serve). Agreed 2026-07-12;
the decision log at the bottom records what was chosen and why.

## Goals & non-goals

**The backend exists to:**

- authenticate users (Google OAuth) and store their personal state: feeds and the sources in
  them, saved posts, settings, home-list order;
- fetch posts from sources (websites, YouTube channels, subreddits) in the background and
  serve them paginated (infinite scroll);
- power the add-wizard's **discovery** (URL or keyword → candidate sources);
- power **post search** scoped to a feed / saved;
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
| **Source** | One RSS endpoint (a website/blog, a YouTube channel, a subreddit). Global, deduplicated, polled once no matter how many users follow it. One source can sit in several of a user's feeds. | Yes (uid `source_*`) — user-facing since 2026-10-08 |
| **Post** | One item of a source. Global, deduped per source by guid. | Yes (uid `post_*`) |
| **Feed** | The user's named **group of sources** — a name, a description and an ordered list of sources, one or many. What the home list shows and the post list reads. Same noun as the frontend's `Feed` type, deliberately. | Yes (uid `feed_*`) |
| **FeedSource** | One source's place in one feed: the user's own name for it there (blank means the source's own title), on/off for that feed, order. Unique per (feed, source). | Not an entity of its own — it flattens into the feed's `sources` list, where the frontend calls each row a `Source` |
| **Saved** | Per-user post→group map; fixed groups Bookmarks / Favorites / Later. | Yes (uids `saved_*`) |

There is no **Folder**: a feed is already the group (removed 2026-10-08, see the decision log).

Merged streams (a feed's read, `all`, `saved`) need no entity name — the polymorphic
`/feeds/{uid}/posts` uid expresses them, mirroring the frontend's resolver order in
[screens-and-flows.md](./screens-and-flows.md).

The **backend mints every public uid** with the prefixes the frontend already resolves:
`feed_*`, `source_*`, `post_*`, plus the literals `all` / `saved` and the fixed `saved_*`
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
   │ FeedSource │            │ SavedPost  │
   └────────────┘            └────────────┘
     │ many   (your name for      (group: bookmarks /
     │ one     it, on/off, order)  favorites / later)
   ┌────────────┐
   │    Feed    │  (name, description, order)
   └────────────┘
   + User · AuthToken · UserSettings
```

Consequences worth spelling out:

- **Adding a source to a feed** is usually "link an existing source" — instant, posts already
  fetched. Only the first user to add a source triggers a fetch.
- **Renaming a source** edits *your* FeedSource row's name, never the shared Source title, and
  **changing its link** swaps which Source the row points at (resolving, and so fetching, the
  new URL) — the shared Source's URL is never edited, since that would repoint everyone else.
- A source that **no feed holds** is orphaned: polling stops (it's deactivated, kept for cheap
  re-adding; a cleanup job can delete stale orphans later).
- Post content (including extracted article text) is cached **globally** — extracted once,
  served to everyone.

## Stack

**Django 5 + django-ninja + Dramatiq (+ periodiq) + Postgres 16 + Redis**, Docker Compose,
living in `backend/` in this repo (monorepo).

| Piece | Job | Why this one |
| --- | --- | --- |
| Django | ORM, migrations, **admin**, management commands | Admin is the free ops UI a feed aggregator needs daily: inspect sources/fetch errors, flip `active`, revoke tokens — zero UI built |
| django-ninja | The API layer | FastAPI's ergonomics (type-hinted endpoints, Pydantic schemas, auto OpenAPI) inside Django |
| Dramatiq + Redis | Background jobs (polling, pruning); the same Redis is Django's cache | Simple, reliable task queue; `periodiq` adds the cron scheduling Dramatiq lacks. The cache holds YouTube search answers for a day so every worker shares one quota spend — never `cache.clear()` it, which on this backend is `FLUSHDB` against the queues' database |
| Postgres | Data **and search** (FTS + trigram) | One store, no sync pipeline — see [Search](#search) |
| feedparser / trafilatura / google-auth | RSS parsing / article extraction / id_token verification | The Python ecosystem is the decisive reason this backend is Python |
| nh3 | Sanitises extracted article HTML before it is stored | The reader renders `article_html` as markup, so the allowlist has to be a rule we own rather than a property of trafilatura's internals; ships abi3 wheels, so the image needs no Rust toolchain |
| requests | The HTTP client ingest, extraction and discovery fetch with | feedparser's own fetching passes no timeout and is removed in feedparser 7 — see the decision log |
| ruff / pytest + pytest-django | Lint + format / tests | One fast tool for both linting and formatting; pytest-django gives the ORM fixtures and a throwaway test database |

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
Source        uid (source_*), type (website|youtube|reddit), feed_url (unique), site_url,
              title, description (the feed's own <description> / <subtitle>, backfilled at
              ingest like the title, flattened to plain text, 1000-char cap), icon_url,
              active, etag, last_modified, last_fetched_at, next_fetch_at, error_count
Post          uid (post_*), source FK, guid (unique per source), title, post_url, image_url
              (the source's URL as fetched — the wire carries a proxied `image` built from it,
              see images.md; stage 2 adds image_key / image_width / image_height),
              summary, article_html (nullable — filled by on-demand extraction),
              published_at, search (persisted generated tsvector, title weighted over summary,
              GIN-indexed) + a functional trigram index on upper(title)
Feed          uid (feed_*), user FK, name, description, order; sources M2M through FeedSource
FeedSource    feed FK (cascade), source FK (PROTECT), name (the user's rename — blank means
              the source's own title), enabled (bool: on/off for this feed), order
              — unique (feed, source)
SavedPost     user FK, post FK, group (bookmarks|favorites|later), saved_at
              — unique (user, post): a post lives in exactly one group
UserSettings  user 1:1, theme, feed_list_style, scrollbar_style, post_card_style, pane_split (posts|equal|post), … (grows with Appearance options)
```

**Cascade rules** are exactly [data-model.md](./data-model.md#cascade-rules)'s, enforced
server-side: removing a source from a feed deletes that one FeedSource row (the feed stays,
even empty); deleting a feed deletes its FeedSource rows; and in both — and when a changed link
swaps a row's source — a source left in no feed of anyone is deactivated, never deleted
(`FeedSource.source` is `PROTECT`, so a followed source can't be removed from under a feed).
Saved posts are untouched by all of it.

**Existing data was not migrated** _(2026-10-08)_: migration `0007_feeds_group_sources` has no
data step. The old feeds and folders were dropped (a fresh start), and saved posts were kept.

**Retention _(built 2026-09-07, T13)_:** a nightly job prunes unsaved posts older than **90
days** and, per source, unsaved posts beyond the newest **500** — both rules delete, so a post
dies if either catches it, and both are tunable for a single run (`manage.py prune_posts
--days --cap --dry-run`). Saved posts are **always kept**, at any age and under either rule, and
the exemption is "saved by anyone": a post row is global, so an owner-scoped rule would delete one
out from under another account's saved pile. **Ingest honours the same window** — polling never
creates a post the prune would delete that night, so an archive feed can't refill what the job
just emptied; the visible consequence is that a source whose entries are all past the window
can still be added, as a valid source with zero posts. Keeps the table and its two GIN indexes lean; a
reader is about recent content.

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

Grouped in the OpenAPI schema — and so in the docs UI at `/api/v1/docs` — under four tags:
**home** (the home aggregate and its reorder), **feeds** (what you follow: the polymorphic post
list, post detail, save, and the writes to feeds and the sources in them), **user** (identity,
sessions, settings), and **default** (`/health`). The tag is declared on each router in
`core/api/`; the order and the per-group descriptions come from `TAGS` in `feedme/api.py`.

**Every feed write answers with the whole feed** (`HomeFeedSchema`, the shape `GET /home` holds
per feed), so the app swaps one row of its home list rather than re-reading `/home` — the one
exception is `DELETE /feeds/{uid}`, which has nothing left to return.

| Method & path | Purpose |
| --- | --- |
| `POST /auth/google` | Body: the Google `credential` (id_token). Verify signature / issuer / audience / expiry → find, link or create the User → issue an opaque bearer token. **Returns the token alone**; the profile comes from `GET /me` |
| `POST /auth/logout` | Revoke the presented token (delete its row) |
| `GET /me` | Profile: email, member-since, sign-in provider (Settings → Account) |
| `DELETE /me` | Delete account + all user data (tokens, feeds and their sources, saved, settings); a source that was nobody else's is deactivated |
| `GET /home` | **One aggregate round-trip for the home screen:** `feeds` in display order — each `{uid, name, description, sources: [{uid, name, title, type, site_url, feed_url, icon, enabled}]}`, where `name` is the user's rename in that feed or else the source's own `title`, and `icon` is a proxied 64px square or null — plus `saved_counts` per group. There is no separate order field and no folders |
| `PUT /home/order` | Persist home-list reorder: the ordered list of feed uids — exactly the account's feeds, no more, no less (a duplicate, unknown or missing uid is a 422 that writes nothing). No UI drives it yet |
| `POST /feeds` | Create a feed: `{name?, description?, feed_url?}`. With a `feed_url` it creates the feed **and its first source in one call**: find-or-create the Source (`type` inferred from the host) and fetch a brand-new one inline — **fetching it is what validates it**, so a URL that isn't a feed answers 422 and leaves neither a Source nor an empty feed behind. Name and description default to the source's own; without a `feed_url` a name is required. 201, returns the feed |
| `PATCH /feeds/{uid}` | Edit the feed: `{name?, description?}` — omitted means untouched |
| `DELETE /feeds/{uid}` | Delete the feed and its placements (204). Any source left in no feed of anyone is deactivated, not deleted |
| `POST /feeds/{uid}/sources` | Add a source to the feed: `{feed_url}`. Same find-or-create-and-fetch as above. 201, returns the whole feed. A source already in this feed is a 422, "That source is already in this feed." |
| `PATCH /feeds/{uid}/sources/{source_uid}` | Edit one placement: `{name?, enabled?, feed_url?}`. `name` is the user's rename (`""` clears it back to the source's title); `enabled` is the on/off for this feed only; a new `feed_url` is resolved (fetched) to a *different* Source and the row is repointed to it, keeping its name and on/off — the shared Source's URL is never edited, and the old source is deactivated if nothing else holds it. A URL that isn't a feed, or one already in this feed, is a 422 and changes nothing |
| `DELETE /feeds/{uid}/sources/{source_uid}` | Remove the source from this feed; 200, returns the feed. A feed may be left empty. The source is deactivated if no feed holds it any more |
| `GET /feeds/{uid}/posts` | **The post list, polymorphic uid:** `all` (sources on in at least one feed) \| `saved` \| `saved_*` \| `feed_*` (that feed's **enabled** sources) — same resolution order as the frontend's `usePostList`. Newest-first, cursor-paginated |
| `GET /posts/{uid}` | Post detail (what RSS gave us). Every post, here and in the lists, carries `source: {uid, name, type, site_url}` — where it came from, `name` being the caller's rename of that source in any feed (the first, in feed order) or else the source's own title; it replaces the earlier `feed_uid`. A post may be opened or saved if its source is in any of the caller's feeds, on or off, or if it is saved. From T15a every post carries `image: {src, srcset} \| null` in place of `image_url` — ready `<img>` attributes built by `core/images.py`, see [images.md](./images.md) § Wire contract. Posts also carry `video: {src, vertical} \| null` (YouTube only), built by `core/youtube.video()` |
| `GET /posts/{uid}/article` | Full article: extract-on-first-request (trafilatura), cached globally in `article_html`, served instantly after. Returns extracted HTML or a "couldn't extract" signal (frontend falls back to summary + Open source). From T15c the `<img src>` inside `article_html` are rewritten to proxied, reading-width URLs at read time — never into the cached column |
| `PUT /posts/{uid}/save` | Body: `{group}` (bookmarks \| favorites \| later). Upsert — moving groups is the same call |
| `DELETE /posts/{uid}/save` | Unsave |
| `GET /discover` | `?type=website|youtube|reddit&q=<url or keyword>` → candidate sources (`name`, `type`, `site_url`, `feed_url`, `icon`, `subscribers`, `already_subscribed`) — a source row's fields minus the uid, `title` and `enabled` it hasn't earned, plus the flag. `already_subscribed` means the source is **in one of your feeds** already; it no longer blocks picking, since a source can sit in several. Field names follow § Vocabulary (`name`, not `title`). A URL resolves under any card; a bare name is a YouTube channel search under `youtube` (503 when YouTube won't answer) and finds nothing under the other two until T11c/T11d. `subscribers` is a YouTube search hit's subscriber count — one extra `channels.list?part=statistics` call per search for all hits (1 quota unit), cached with the search; null for a hidden count, a pasted URL, or any other type, and a failed statistics call leaves it null without failing the search (and isn't cached) _(2026-10-08)_. Backs the add wizard |
| `GET /discover/posts` | _(T14, planned)_ `?feed_url=<a candidate's feed_url>` → its newest 10 posts, fetched live and never stored — `PostSchema` minus `uid` / `source` / `saved_group`, with `published_at` nullable. The twin of `GET /feeds/{uid}/posts` for a source you haven't added yet. Unreachable or not a feed → 422 with a message; a real feed with no entries → `[]` |
| `GET /search` | `?q=&scope=<all \| saved \| saved_* \| feed_*>&cursor=&limit=` (scope defaults to `all`) — **the post list narrowed by `q`**: same polymorphic scope uid, same page shape, same cursor, newest-first. A blank `q` is an empty page, not an error. Engine-neutral contract — no tsquery syntax in, no rank out; see [Search](#search) |
| `GET /settings` · `PUT /settings` | The persisted `UserSettings` (theme, feed-list style, post-card style, desktop `pane_split`, …) — replaces cookie-only persistence so settings follow the account across devices |

## Auth

**Google OAuth only in v1** — verified directly with `google-auth`, since one provider doesn't
need an auth framework; allauth stays the answer if a second one ever justifies it, and Apple
becomes relevant when the iOS app ships. The app is **login-only** — no guest mode.

Flow (**built on web** as of 2026-09-03; the Capacitor half of step 1 is not):

1. Frontend obtains a Google **id_token** — Google Identity Services on web, the native
   Google Sign-In plugin under Capacitor. Google's UI does the heavy lifting: on web that means
   **its own rendered button**, whose chrome we don't control. A fully custom control would be
   the OAuth *code* flow, a different exchange needing a server-side secret.
2. `POST /auth/google` with the id_token. Backend verifies the signature against Google's
   published keys (`google-auth`), checks issuer/audience/expiry, requires a **verified** email,
   then resolves the account: by Google `sub`; else onto an existing row with the same email
   **only if no Google account has claimed it** (attach the `sub` — a collision answers 401);
   else create.
3. Backend issues an **opaque bearer token**: 32+ random bytes, stored **SHA-256-hashed**
   (a DB leak leaks no live sessions), **sliding 30-day expiry** (touched on use). The
   frontend stores it (cookie/localStorage on web, secure storage on native) and sends
   `Authorization: Bearer …` on every call.

Only a **client id** is involved — an id_token is verified against public keys, so no client
secret exists in this flow and none is stored. The id is optional on both sides: without it the
sign-in screen renders no Google button and the backend refuses to verify anything, which is a
degraded app rather than a broken one.

**A dev-token path still exists beside it, temporarily.** `manage.py issue_token <email>` mints a
working bearer token (T2), and `/login` keeps a field for pasting one below Google's button, so an
account with no Google identity can still be signed into. It is scheduled for removal — see
[backend-roadmap.md](./backend-roadmap.md) § Decision log (T8). `GET /me`'s `provider` describes
the **account**, not the session: a linked account reports `google` even in a session started with
a pasted token.

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
  fetch it once and either parse it as a feed or read the `<link rel="alternate">` tags off the
  page, walking up the path if the page itself declares none; keyword search only matches **our
  own source catalog** in v1 (no web-crawl index — that's a Feedly-scale product we're not
  building).
- **YouTube** — channels expose plain RSS: `youtube.com/feeds/videos.xml?channel_id=…`, so
  **polling needs no API quota**. A pasted channel URL or `@handle` needs none either — the
  channel page declares that same feed. The Data API is used only for *keyword* discovery
  _(built 2026-09-11, T11b — `core/youtube.py`)_: `search.list` costs 100 of the day's 10k
  units (≈ 100 searches), so every answer is cached for a day, a failed one is not, and a
  missing `YOUTUBE_API_KEY` degrades to the paste path rather than erroring. YouTube not
  answering is a 503, never an empty list. **In the reader**, a YouTube post's `video`
  _(built 2026-09-28 — `core/youtube.video()`)_ is `{src, vertical} | null`, derived from
  `post_url` alone: a `youtube-nocookie.com` embed (`playsinline=1`, `rel=0`), `vertical` for a
  `/shorts/` link. At ingest the post's `hqdefault` thumbnail is upgraded to `hq720.jpg` when a
  `HEAD` request finds it (answer cached 30 days; a network failure is not cached).
- **Reddit** — subreddits expose RSS/JSON; polling uses a single registered **app token**
  (rate limits are generous at our scale: ~100 QPM ≫ thousands of subreddits at 30-min
  intervals). Unauthenticated `.rss` fetches are *not* generous — Reddit answers 429 to repeated
  ones, which is why discovery needs the same app token. Per-user Reddit account connect (the
  Feedly pattern) stays **deferred** — revisit only if app-level limits bite.

**Fetching somebody else's URL is one module.** `core/fetch.py` holds the scheme allowlist, the
per-hop private-address check and the size cap, and both callers that hand a fetched body back to
the requester go through it: article extraction (`core/extract.py`) and discovery
(`core/discover.py`). Polling deliberately does not — `core/ingest.py` only ever stores what it
parses, so it fetches plainly. The knobs differ per caller (extraction wants HTML only and refuses
past 2 MB; discovery reads a feed *or* a page and truncates instead of losing it), the guard does
not.

**Jobs** (Dramatiq; cron via periodiq — actors in `core/tasks.py`, broker wiring in
`feedme/broker.py`). `poll_source` is a Dramatiq actor wrapping `core/ingest.py`'s
`ingest_source` with no rewrite, and the two prune actors wrap `core/retention.py`'s plain
functions the same way; `manage.py poll_source <source_uid>` and `manage.py poll_due`
still call `ingest_source` directly, as the manual override:

| Job | Trigger | What it does |
| --- | --- | --- |
| `poll_source` | periodiq's cron sweep (`poll_due_sources`, every 5 minutes) enqueues sources with `next_fetch_at` due (targets ~30-min per-source cadence, staggered), claiming each one before sending | Conditional GET (ETag / Last-Modified — most polls are cheap 304s), parse, upsert posts by (source, guid) — never *creating* one already past the retention window — reset `error_count` |
| `prune_posts` | Daily, 03:30 | Delete unsaved posts past the 90-day window, plus — per source — those beyond the newest 500; a post goes if either rule catches it, and a saved post never goes at all (see [Data model](#data-model)). Batched deletes; `manage.py prune_posts --days --cap --dry-run` is the manual override |
| `prune_expired_tokens` | Daily, 03:45 | Delete `AuthToken` rows past the sliding 30-day window — rows the guard already answers 401 for, so the sweep can end no live session |
| failure handling | on poll error | Increment `error_count`, back off (grow `next_fetch_at`), deactivate after N consecutive failures — all visible/reversible in admin |

**Article extraction is not a job.** `GET /posts/{uid}/article` extracts inside the request that
asked for it — `core/extract.py`, synchronous with a hard timeout — because the reader is
blocked on the answer either way; queueing it would buy a free web thread at the cost of a
polling loop and a third state on screen. A post is extracted once and served to everyone after,
so the slow path is rare. This fetch also has rules polling doesn't need — a scheme allowlist, a
per-hop private-address check and a size cap — because unlike ingest, which only stores what it
parses, this endpoint hands the fetched body back to the caller. **YouTube posts skip it
entirely** and answer "couldn't extract": a watch page is a JS shell with no article in it, and
the player plus the description is the right treatment for a video anyway. See
[backend-roadmap.md](./backend-roadmap.md) § Decision log (2026-09-05, T10), which records the
reversal of this table's earlier `extract_article` job row.

## Search

**Postgres FTS + pg_trgm. No separate search engine in v1** — decided after a detailed
Elasticsearch comparison (see decision log). **Built _(2026-09-06, T12)_:** `GET /search`
answers, and the post list (mobile page and desktop posts pane) searches through it from the
list's title row ([screens-and-flows.md](./screens-and-flows.md) § 2).

The use case is *scoped* search: part of a title, within one feed / saved list.
That never hits FTS's real scale cliff (ranking huge unscoped result sets), and every ES
advantage either doesn't activate on scoped queries or belongs to features FeedMe rejects
(trending, recommendations) or defers (public lists).

Design:

- `Post.search` is a **persisted generated `tsvector`** — `title` (weight A) over `summary`
  (weight B), both with the `english` dictionary — with a **GIN index**. Postgres recomputes
  it in the same statement that writes the row, so search is never stale and there is no sync
  pipeline. A **functional trigram index** on `upper(title)` (pg_trgm) covers partial-word
  matching ("rout" → "router"), which FTS's whole-word lexemes structurally cannot reach; a
  query is the two branches OR'd. `summary` is matched whole-word only — it is arbitrary
  third-party HTML, so substring-matching it would match markup.
- Scoping is not a second implementation: `scope` resolves through the same `core/postlist.py`
  uid resolver the post list uses, joining the live Feed/FeedSource/SavedPost tables — switch a
  source off in a feed and search reflects it instantly, with no re-index.
- Results are ordered by **recency, not relevance**. The weights are in the vector, so ranking
  later is an `order_by` rather than a migration, and today's results reuse the post list's
  cursor unchanged.
- **The engine is hidden behind the contract.** `GET /search` takes `q` + `scope` + cursor
  and returns posts — no tsquery syntax, no raw rank scores. All search SQL lives in **one
  backend search module** (`core/search.py`); nothing else touches the tsvector column, and a
  test enforces that rather than a convention. The post table stays the source of truth — any
  future index is derivable from it.

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
| `worker` | `dramatiq core.tasks --processes 2 --threads 4` — runs the actors in `core/tasks.py` |
| `scheduler` | `periodiq -v core.tasks` — the cron sweep; enqueues, never executes |
| `db` | Postgres 16 |
| `redis` | Redis (Dramatiq broker) |
| `imgproxy` | the image proxy — resizes and converts every image the app shows, from a signed URL `core/images.py` builds; nothing stored. Stage 2 adds `minio` (the dev bucket). See [images.md](./images.md) § Operations |

`api`, `worker` and `scheduler` are one image behind three different commands —
`docker-compose.yml`'s `x-backend` YAML anchor shares the build, the bind mount and the
environment so the three can't drift apart; `worker` and `scheduler` skip the migrate/bootstrap
entrypoint and wait on `api`'s healthcheck instead, since only `api` should touch the schema.

Everything Python runs in the `api` container — tests and linting included:

```bash
docker compose exec api pytest        # config + fixtures in backend/pyproject.toml, backend/conftest.py
docker compose exec api ruff check .  # lint; `ruff format .` to reformat
```

A gitignored `.venv/` at the repo root mirrors `requirements.txt` so the IDE can resolve
imports, and it also backs the PostToolUse hook that runs `ruff check --fix` + `ruff format` on
every `.py` Claude edits — so it is no longer optional on a fresh machine, though the app itself
never runs from it (`db` publishes no host port). Recreate it with
`python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt`.

The Nuxt dev server keeps running via `pnpm dev` as today, talking to `api` on localhost.
Production topology (reverse proxy, frontend build/hosting) is **deferred** — nothing in
this spec constrains it. Credentials (the Google **client id** — there is no client secret in
this flow — the YouTube API key, Reddit app credentials) live in an env file, never in git. The
Google client id appears there **twice**: compose passes `GOOGLE_OAUTH_CLIENT_ID` to `api`, and
Nuxt reads the same value as `NUXT_PUBLIC_GOOGLE_CLIENT_ID` — public by design, since it ships in
the page that renders the button.

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

Added 2026-08-19 (T1):

- **`django-cors-headers` over a Nuxt dev proxy** — Capacitor is planned, and a native app calls
  from `capacitor://localhost` with no Nuxt dev server in front of it. Solving CORS in Django
  covers web, native and production; a proxy covers only web dev.
- **`pytest` + `pytest-django` from T1** — folder cascades, the uid resolver, cursor boundaries
  and token expiry regress silently. Tests land with the task that creates the logic.
- **`ruff` for both lint and format**, curated rule set (`E, W, F, I, UP, B, DJ`), single quotes,
  migrations excluded.
- **Per-user Reddit connect deferred**; app-token polling suffices at v1 scale.

Added 2026-08-25 (T3):

- **`requests` does the HTTP; feedparser only parses.** feedparser can fetch a URL itself, but
  that path gives urllib no timeout — the only bound would be the process-global
  `socket.setdefaulttimeout()`, which in the `api` container also covers Postgres and Redis
  sockets. Upstream removes those HTTP arguments in feedparser 7 and points callers at an HTTP
  client, so `requirements.txt` pins `feedparser<7` and ingest fetches for itself. It also gives
  the tests one seam to fake instead of monkeypatching a third-party module's internals.
- **Ingest never raises.** Network errors, HTTP error statuses and bodies that aren't feeds all
  land in the same recorded-failure path: `error_count` up, `next_fetch_at` out exponentially
  (capped at 24h), deactivated at five consecutive failures, reversible from an admin action.
  A poller that can throw is a poller that stops polling everything behind it.

Added 2026-08-23 (T2):

- **One error body for the whole API: `{"detail": string}`** — ninja already answers 401 and
  404 in that shape, so only the 422 handler is overridden (its default detail is a list of
  pydantic dicts). Each operation declares `401: ErrorSchema` so the shape reaches the OpenAPI
  schema; T6 generates TypeScript from it, and a single-shaped error is one generated type
  rather than a union.
- **Expired tokens are rejected, not deleted**, and `last_used_at` is touched at most once an
  hour — an unauthenticated caller can never force a database write, and an authenticated
  request stays a single indexed read.

Added 2026-09-03 (T8) — both are `google-auth` traps, not product choices:

- **An unset client id must never reach the verifier.** `verify_oauth2_token(token, request,
  None)` skips the audience check *entirely* rather than failing, so an unconfigured server would
  accept an id_token minted for somebody else's app. `core/google_auth.py` raises while
  `GOOGLE_OAUTH_CLIENT_ID` is empty, and a test pins that.
- **Catch `GoogleAuthError` as well as `ValueError`.** A bad signature, a malformed or expired
  token and a wrong audience all raise `ValueError`, but a wrong *issuer* raises
  `GoogleAuthError`, which is **not** a `ValueError` subclass — catching only `ValueError` would
  turn a rejected token into a 500.

Added 2026-09-07 (T13):

- **Polling and pruning agree on one line.** `core/ingest.py` reads `core/retention.py`'s
  `age_cutoff()` and never *creates* a post the nightly prune would delete. Without that the two
  jobs fight over the same rows forever — an archive feed serves far more than a retention window,
  so the next poll simply recreates what was deleted (observed: 49 posts back within five minutes,
  with fresh uids and empty article caches) and the table never gets lean. Entries already stored
  are still updated, so a saved post that has aged out keeps tracking its source. The consequence
  belongs to the contract, not just the job: subscribing to a feed whose entries are all past the
  window **succeeds and yields zero posts**, since `POST /feeds` only refuses a URL with no
  entries at all.

Added 2026-09-15 (images strategy, before T15a):

- **Images go through a proxy the backend signs for; the frontend never builds an image URL.**
  A new `imgproxy` service resizes on demand from signed URLs that `core/images.py` alone knows
  how to build — the containment rule `core/search.py` already follows. Staged: nothing stored
  first (T15a), originals copied into a bucket at ingest next (T15d), a CDN and, if ever needed,
  a paid transformer at deploy (T15e) — each a change inside that one module. Pre-rendering
  sizes at ingest (the previous project's shape) was rejected because a new size then means a
  backfill over every post. The full comparison and the wire contract are in
  [images.md](./images.md) § Decision log.

Added 2026-10-08 (the feeds remodel, outside the numbered tasks):

- **No folders: a `Feed` is the group.** The user's call: "lets not have folders. we simple have
  feeds and sources. feed is like a folder, its a group of sources. feed has title description
  and list of sources. feed can also have a single source." This **supersedes** the 2026-07-12
  entry that made `Feed` the user↔source link, and every folder rule built on it. `Feed` keeps
  its name and its place in the shared vocabulary but now means the group; the link moves to
  `FeedSource`. The shape of the feed page came from a screenshot of crowdfeed, the user's
  earlier aggregator.
- **`Source` is user-facing** (uid `source_*`). The earlier "only `Source` is backend-only" no
  longer holds: the user now sees, renames, relinks and switches sources. `FeedSource` stays a
  backend noun — the wire flattens it into the feed's `sources` list.
- **One source can sit in several feeds, with its own name and on/off in each.** Both live on
  `FeedSource`, unique per (feed, source). On/off is a property of the placement and replaces
  the old per-folder mute: a feed's stream is its enabled sources, and `all` is every source
  enabled in at least one feed.
- **Renaming is per placement; relinking swaps the Source.** The shared `Source.feed_url` is
  never edited — that would repoint every other reader — so a new link is resolved (fetched, so
  validated) to a different Source and the row is repointed, keeping its name and on/off. The
  old source is deactivated if nothing else holds it.
- **A feed may be empty.** Removing its last source leaves the feed standing: deleting it for
  the user would throw away the name and description they wrote.
- **Every feed write answers with the whole feed** (`HomeFeedSchema`), so the app swaps one row
  of its list; the server's view of a rename's fallback title or a new link lands exactly.
- **Posts carry `source: {uid, name, type, site_url}`, replacing the nullable `feed_uid`.** A
  post always has exactly one source, so the field is never null and a saved post keeps saying
  where it came from after that source leaves every feed. `name` is the caller's rename of that
  source in any feed (the first, in feed order), else the source's own title.
- **A post can be opened or saved if its source is in any of the caller's feeds — on or off —
  or if it is saved.** Off removes a source from streams only.
- **`already_subscribed` stays on `/discover`, but now means "in one of your feeds"** and no
  longer blocks picking: the same source can legitimately join another feed.
- **`Source.description` is backfilled at ingest** from the feed's own RSS `<description>` /
  Atom `<subtitle>` — `strip_tags` + `unescape`, whitespace collapsed, capped at 1000 — and
  seeds a new feed's description. Like the title it only fills a blank, and it is not on the
  wire.
- **Fresh start, no data migration.** Migration `0007_feeds_group_sources` drops `Folder` /
  `FolderMember` and reshapes `Feed`; the old feeds and folders were dropped and saved posts
  kept, so there was nothing to translate.
