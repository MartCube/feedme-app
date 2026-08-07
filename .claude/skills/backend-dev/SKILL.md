---
name: backend-dev
description: Work on the FeedMe Django backend — compose workflow, django-ninja conventions, and the vocabulary the API must share with the frontend
---

# FeedMe backend

Django 5.2 + django-ninja in `backend/`, Postgres 16 + Redis via `docker-compose.yml`.
`docs/backend.md` is the spec — read the relevant section before building; this skill is
the working shorthand.

**Status check first.** The backend is early: `backend/feedme/api.py` may still be little
more than `/health`. Read what actually exists before assuming a model or endpoint is
there.

## Running it

```bash
docker compose up -d db redis     # deps only
docker compose up api             # Django on :8000
docker compose logs -f api
```

Django commands run *inside* the `api` service — the host has no venv:

```bash
docker compose exec api python manage.py makemigrations
docker compose exec api python manage.py migrate
docker compose exec api python manage.py shell
```

`backend/` is bind-mounted, so edits reload without a rebuild. Rebuild only after
touching `requirements.txt` or the `Dockerfile`: `docker compose build api`.

The Nuxt dev server stays on `pnpm dev` and talks to `api` on localhost — the frontend is
never containerised for development.

## Vocabulary — this is the load-bearing rule

Backend code, API responses, and the frontend share **the same nouns**. Drift here is the
expensive mistake, and enterprise-speak is vetoed (`Subscription` was rejected in favour
of `Feed`).

| Term | What it is | Public? |
|---|---|---|
| **Source** | One RSS endpoint. Global, deduplicated, polled once regardless of follower count. | No — backend-only |
| **Post** | One item of a source. Global, deduped per source by guid. | Yes — `post_*` |
| **Feed** | The user↔source link: *your* handle on a source (custom name, order). Same noun as the frontend's `Feed` type, deliberately. | Yes — `feed_*` |
| **Folder** | A user's named group of feeds; many-to-many, per-folder mute. | Yes — `folder_*` |
| **Saved** | Per-user post→group map; fixed groups Bookmarks / Favorites / Later. | Yes — `saved_*` |

**The backend mints every public uid** with the prefixes the frontend already resolves:
`feed_*`, `folder_*`, `post_*`, plus literals `all` / `saved` and the fixed `saved_*` group
uids from `app/utils/saved.ts`. Mock ids (`art_med_1`) are replaced by `post_*`.

Merged streams (a folder's read, `all`, `saved`) get no entity name — the polymorphic
`/feeds/{uid}/posts` uid expresses them, mirroring the frontend's resolver order.

Before naming a new model, field, or endpoint: check the table above and `docs/backend.md`
§ Vocabulary. A new public noun is a discussion, not a unilateral call.

## django-ninja conventions

- Routes hang off the `NinjaAPI` in `backend/feedme/api.py`; group by resource with
  `Router` as the catalogue grows (`docs/backend.md` § Endpoint catalog is the contract).
- Request/response shapes are **ninja `Schema` classes**, not bare dicts — the frontend's
  types are generated from this contract's shape.
- Schema field names are the API's public surface: `snake_case`, matching the vocabulary
  table. Never leak a `Source` to the frontend; it's backend-only.
- Return the uid, never the integer pk.

## Ground rules

- **Secrets never enter git.** Google client id/secret, YouTube API key, Reddit
  credentials live in `.env` (gitignored). Add the *key* to `.env.example` with an empty
  or placeholder value; a hook blocks `.env` edits outright.
- Migrations are generated, never hand-written, and get committed alongside the model
  change.
- No Python lint config exists yet. If the backend grows past a few modules, propose
  `ruff` — don't add it silently.
- `docs/backend.md` § Decision log records *why*. Append there when a choice is made;
  don't rewrite past entries.
