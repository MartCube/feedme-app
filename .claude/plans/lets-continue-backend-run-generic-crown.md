# T4 review + T5 plan — Posts: list, detail, save

## Context

T4 (`/home`, `/home/order`, `/settings`) landed in `f33366c`. Before moving on, this reviews
what shipped, then plans **T5 — Posts: list, detail, save** (`docs/backend-roadmap.md` § T5).

T5 is the last backend task before T6 wires the Nuxt app to real data, so its shapes are the
ones `openapi-typescript` will generate the frontend's `Post` type from. It is also the first
endpoint whose response depends on *who is asking* for reasons beyond a `user` filter: posts
are global rows, and the same `Post` carries a different `feed_uid` and `saved_group` per
caller.

---

## Part 1 — T4 review

**Verified.** `docker compose exec api pytest` → **77 passed**. `ruff check .` → clean.
`ruff format --check .` → 35 files already formatted.

The implementation is correct and the test coverage is real (isolation, query count pinned at
5, order round-trip, every 422 branch, drift guards on the `Literal`s). Four findings, none of
them a live bug:

1. **`set_home_order` validates outside the transaction** (`backend/core/api/home.py:96-114`).
   Folders, feeds and the nested set are read, validated, and only then is `transaction.atomic()`
   entered. Two devices reordering at once can both pass validation and the second write lands
   an order derived from a list that no longer exists. `select_for_update()` over the user's
   folders and feeds inside the transaction closes the concurrent-*reorder* case; it does not
   close a concurrent *subscribe* (no gap locks under READ COMMITTED), which would leave the new
   feed at `order = 0`.
   **Recommendation: don't fix now.** The drag-and-drop UI that would trigger it doesn't exist
   yet, the failure is cosmetic (a misplaced row, corrected by the next `/home`), and a partial
   fix that reads as complete is worse. Record it in the roadmap's decision log with T7 as the
   trigger.

2. **`SavedCountsSchema` has no drift guard** (`backend/core/api/home.py:47`). Its three keys are
   written out separately from `SavedPost.Group`, exactly like `HomeFeedSchema.type` and the
   settings `Literal`s — both of which T4 pinned with a test. This one wasn't. A fourth group
   would be silently dropped from `saved_counts`. **Fix in T5**, which is the task that makes
   saved groups load-bearing.

3. **`PUT /home/order` has no 401 test.** `test_home_401s_without_a_token` covers the `GET` only.
   The guard is global so coverage is structural, but the pattern elsewhere is one per operation.
   **Fix in T5** — one line.

4. **Two edges T4 created that T7 has to honour**, worth recording now while the reasoning is
   fresh:
   - `Feed.order` is never normalised for feeds inside folders, so a feed removed from a folder
     becomes top-level carrying a stale `order` (usually `0`) and lands in an arbitrary spot.
     `PATCH /folders/{uid}` / `DELETE /folders/{uid}` need to assign it a fresh position.
   - `FolderMember` has no constraint that `folder.user == feed.user`. Unreachable today, but
     `PATCH /folders/{uid}`'s set-members path must verify every feed uid belongs to the caller.

**Actions folded into T5:** findings 2 and 3 (two tests). Findings 1 and 4 become decision-log /
roadmap entries, no code.

---

## Part 2 — T5 build plan

### Decisions settled before building

- **Saved streams order by `saved_at` desc**, not `published_at` — `saved` / `saved_*` read as a
  "recently saved" pile. Costs a second cursor basis; every other stream stays on `published_at`.
- **Post access is owner-scoped**: a post is readable and savable only if the caller subscribes
  to its source *or* has already saved it. 404 otherwise. The `or saved` half is what keeps a
  saved post readable after you unsubscribe.
- **`feed_uid` is nullable.** It resolves source → *the caller's* `Feed` uid (§ Contract
  resolutions, item 1), and a saved post whose feed you later dropped has no feed to point at.
  Never hide the post; return `null`. Costs the frontend nothing today — `PostCard.vue` renders
  date + title only and doesn't read `feed_uid`.
- **The cursor encodes the timestamp + the post's public `uid`**, not the integer pk. The
  `backend-dev` skill's rule is "return the uid, never the integer pk", and base64 is decodable
  — an opaque-looking blob holding a pk still exposes it. `uid` is unique and indexed, so it is
  a valid tiebreak.
- **No new index.** `Post` already has `Index(['source', '-published_at'])`, which covers the
  per-source scan the merged streams merge over. Adding a `uid` tiebreak column would fatten the
  index for a case that fires only on identical timestamps, and T13 caps the table anyway.
  Revisit if `EXPLAIN` on a real page request ever shows a sort.

### New module — `backend/core/postlist.py`

Owns uid → posts, and the cursor. One module so the resolution order lives in a single place on
each side (`app/utils/feed-title.ts` is the frontend's copy).

- `resolve_stream(user, uid) -> Stream` — a small frozen dataclass of `(queryset, order_field)`.
  Resolution order is the frontend's exactly: `all` → `saved` → `saved_*` → `folder_*` (members
  minus muted) → `feed_*`; anything else raises 404.
  **Every branch starts from `Feed.objects.filter(user=user)`** — a folder uid is looked up on
  the caller's folders and its members resolved through the caller's feeds, so another user's
  uid is a 404 rather than a leak.
- `annotate_for(user, queryset)` — attaches the three per-caller fields with correlated
  `Subquery`s: `feed_uid` (over `Feed`, unique per `user, source`), `saved_group` and `saved_at`
  (over `SavedPost`, unique per `user, post`). Each resolves to exactly one row.
  **Trap to avoid:** don't express saved membership as `filter(saves__user=user)` plus an
  `annotate(F('saves__saved_at'))` — Django's join reuse across `filter`/`annotate` on a
  multi-valued relation is subtle and can duplicate rows. Select membership with
  `id__in=SavedPost.objects.filter(user=user).values('post_id')` (a semi-join, no duplicates)
  and get the values from the subquery annotations.
- `visible_posts(user)` — `Q(source__feeds__user=user) | Q(id__in=<saved post ids>)`, the access
  rule above, used by detail and both save operations.
- `encode_cursor(post, field)` / `decode_cursor(cursor, field)` — base64url of
  `f'{value.isoformat()}|{post.uid}'`. Decode returns the keyset predicate
  `Q(field__lt=value) | Q(field=value, uid__lt=uid)` and raises 422 on anything malformed.
  T12's search reuses both.

### New module — `backend/core/api/posts.py`

Mounted at `''` in `backend/feedme/api.py` alongside the existing three routers.

| Operation | Response |
| --- | --- |
| `GET /feeds/{uid}/posts?cursor=&limit=` | `200 PostPageSchema`, `401`, `404`, `422` |
| `GET /posts/{uid}` | `200 PostSchema`, `401`, `404` |
| `PUT /posts/{uid}/save` | `200 SavedSchema`, `401`, `404`, `422` |
| `DELETE /posts/{uid}/save` | `204`, `401`, `404` |

- `PostSchema`: `uid`, `feed_uid: str | None`, `title`, `post_url`, `image_url`, `summary`,
  `published_at`, `saved_group: Literal['bookmarks','favorites','later'] | None`. `summary`, not
  `content` — § Contract resolutions, item 2; `article_html` is T10 and never appears here.
- `PostPageSchema`: `items: list[PostSchema]`, `next_cursor: str | None`. Fetch `limit + 1` rows
  to decide whether there's a next page; `null` means the end.
- `limit: int = Query(10, ge=1, le=100)` — ninja 422s an out-of-range value for free, the same
  reason T4 chose `Literal` over `str`.
- `PUT .../save` body is `{group}` typed as the same `Literal`. Upsert via `update_or_create` —
  moving between groups is the same call. Returns `{group, saved_at}`.
- `DELETE .../save` is idempotent: 404 if the post isn't visible, 204 whether or not a
  `SavedPost` row existed. A double-tapped save toggle shouldn't error.
- Follow the existing style: `Status(204, None)` (not the deprecated tuple), `ErrorSchema`
  declared on every operation, `HttpError(404, …)` for the `{"detail": string}` body.

### Tests — `backend/tests/test_posts.py`

Reuse the `make_feed` / `make_folder` / `make_post` fixtures in `backend/conftest.py` as-is;
create `SavedPost` rows inline as `test_home.py` already does. No conftest changes expected.

**Resolution:** every branch returns the right set; `folder_*` excludes a muted member while
that member's own `feed_*` page stays complete; `all` ignores mute (mute is per-folder by
definition); an unknown uid and another user's folder/feed uid are both 404.

**Per-caller fields:** two users subscribed to the same source each get their own `feed_uid`
for the same global post; a saved post whose feed was unsubscribed still lists with
`feed_uid: null`; `saved_group` is `null` when unsaved and the group name when saved.

**Cursor:** paging while a newer post is inserted mid-scroll skips nothing and repeats nothing
(the roadmap's stated reason for keyset over offset); the last page returns `next_cursor: null`;
a malformed cursor is 422; `limit=0` and `limit=1000` are 422.

**Saves:** create, move between groups (still one row, per the `unique(user, post)` constraint),
delete, delete-when-not-saved → 204, and save/read a post you neither subscribe to nor have
saved → 404.

**Cost:** pin the list endpoint's query count and prove it's constant regardless of page size,
mirroring `test_home_costs_the_same_number_of_queries…`. Expect 3 (token, stream resolution,
the page).

**Plus the two T4 gaps:** a `SavedCountsSchema` ↔ `SavedPost.Group` drift guard and a
`PUT /home/order` 401, both in `backend/tests/test_home.py`.

### Docs (delegate to the `docs` agent before committing)

- `docs/backend-roadmap.md` — § Status → T5 done / next T6, the T5 checkbox, a "Decided … while
  building T5" block (saved_at ordering, uid-based cursor, owner-scoped access, nullable
  `feed_uid`, no new index), the two T7 obligations from review finding 4, and the deferred
  `set_home_order` race from finding 1.
- `docs/backend-roadmap.md` § Contract resolutions, item 1 — amend to say `feed_uid` is `null`
  when the caller has no feed for the post's source. Same edit in `docs/data-model.md`.
- `docs/current-state.md` — the T5 paragraph.

## Verification

1. `docker compose exec api pytest -q` — green, including the new `test_posts.py`.
2. `docker compose exec api ruff check .` and `ruff format --check .` — clean.
3. Against the real dev data seeded in T3 (three sources, 50 posts), through ninja's docs UI at
   `http://localhost:8000/api/v1/docs` with a token from `manage.py issue_token`:
   - `GET /feeds/all/posts` returns posts from all three sources, newest first, each with its
     own `feed_uid`.
   - Page through with the returned `next_cursor` until it comes back `null`; no post appears
     twice and none is missing.
   - `PUT /posts/{uid}/save` with `bookmarks`, re-read the list, confirm `saved_group` flipped;
     `GET /feeds/saved_bookmarks/posts` returns it; `DELETE` removes it.
   - `GET /home` afterwards shows `saved_counts.bookmarks` incremented — the two features agree.
4. Confirm `/api/v1/openapi.json` carries `PostSchema` with the nullable `feed_uid` and the
   `saved_group` union, since that's what T6 generates TypeScript from.
