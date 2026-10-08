---
paths:
  - "backend/**/*.py"
---

# Backend rules

Django 5.2 + django-ninja. `docs/backend.md` is the spec — its § Vocabulary and § Decision log
are law; `docs/backend-roadmap.md` § Status says what to build next. The `backend-dev` skill has
the compose workflow.

## Vocabulary — the same nouns as the frontend, no enterprise-speak

| Term | What it is | Public? |
|---|---|---|
| **Source** | One RSS endpoint. Global, deduplicated, polled once. Shown as a feed's sources. | `source_*` |
| **Post** | One item of a source, deduped per source by guid. | `post_*` |
| **Feed** | A user's named group of sources — one or many, each on/off and renameable in it (`FeedSource`). (`Subscription` was vetoed; folders were retired 2026-10-08.) | `feed_*` |
| **Saved** | Per-user post→group map; fixed groups Bookmarks / Favorites / Later. | `saved_*` |

The backend mints every public uid. A new public noun, field, or endpoint name is a discussion,
not a unilateral call.

## API shape

- Routes hang off the `NinjaAPI` in `feedme/api.py`, grouped by resource `Router`;
  `docs/backend.md` § Endpoint catalog is the contract.
- Request/response shapes are ninja `Schema` classes, never bare dicts — the frontend's types
  are generated from them. Field names are `snake_case` and match the vocabulary. Return uids,
  never integer pks.

## Fetching anything from the internet

- **Every outbound request to a user- or feed-supplied URL goes through `core/fetch.py`** —
  `fetch_url` / `check_public` / `read_capped`: http(s) only, public addresses only (re-checked
  on every redirect hop), size-capped reads. Never a bare `requests.get` on such a URL — the
  image proxy, previews, discovery and extraction all share this path.
- HTML that will be rendered as markup passes through the `nh3` allowlist in
  `core/extract.py`. No other sanitizer, no `mark_safe`.
- Fetch/parse features are verified against real, messy URLs, not only fixtures.

## Ground rules

- Migrations are generated (`makemigrations` inside the `api` container), never hand-written
  (hook-guarded), and are committed with the model change.
- Secrets never enter git: add the *key* to `.env.example` with a placeholder; `.env` is
  hook-guarded.
- ruff (`backend/pyproject.toml`) runs on every edit via a PostToolUse hook and **F401 deletes
  an import the moment it is unused** — put an import and its first use in the same edit.
- `worker` and `scheduler` don't autoreload; after editing what they import (`core/ingest.py`,
  `core/retention.py`, `core/tasks.py`): `docker compose restart worker scheduler`.
- Tests (`pytest` + `pytest-django`, `backend/tests/`) are written *with* the task that creates
  the logic, run inside the container: `docker compose exec -T api pytest -q`.
- `docs/backend.md` § Decision log records *why* — append, never rewrite past entries.
