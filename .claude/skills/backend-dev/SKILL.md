---
name: backend-dev
description: Work on the FeedMe Django backend — the compose workflow, the host venv, and where the hard rules live
---

# FeedMe backend

Django 5.2 + django-ninja in `backend/`, Postgres 16 + Redis via `docker-compose.yml`.
`docs/backend.md` is the spec — read the relevant section before building; this skill is
the working shorthand. **`docs/backend-roadmap.md` says what to build next** — its § Status
names the current task; update it when the task lands.

**Status check first.** Read what actually exists (`backend/feedme/api.py`, `backend/core/`)
before assuming a model or endpoint is there.

**The hard rules load themselves.** `.claude/rules/backend.md` is path-scoped to
`backend/**/*.py` and enters context when you read any backend file: the vocabulary table,
ninja `Schema` conventions, the `core/fetch.py` rule for anything that touches the internet,
generated migrations, the ruff F401 trap, and the worker/scheduler restart. Read a sibling
module first when creating a new one.

## Running it

```bash
docker compose up -d db redis     # deps only
docker compose up -d api          # Django on :8000 — always -d; the Bash guard blocks foreground
docker compose logs -f api        # the stream, run backgrounded
```

Django commands run *inside* the `api` service — that's where Django actually executes:

```bash
docker compose exec api python manage.py makemigrations
docker compose exec api python manage.py migrate
docker compose exec api python manage.py shell
docker compose exec -T api pytest -q
```

`backend/` is bind-mounted, so edits reload without a rebuild (`api` only — `worker` and
`scheduler` need `docker compose restart worker scheduler`). Rebuild only after touching
`requirements.txt` or the `Dockerfile`: `docker compose build api`.

The Nuxt dev server stays on `pnpm dev` and talks to `api` on localhost — the frontend is
never containerised for development.

### The host venv is for the IDE and the lint hook only

`.venv/` at the repo root (gitignored) mirrors `requirements.txt` so the IDE can resolve
`django`/`ninja` imports and the PostToolUse hook can run `ruff` — **nothing else runs from
it**. Recreate on a fresh machine with
`python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt`, then point the
IDE at `.venv/bin/python` and mark `backend/` as the sources root (imports are rooted there,
not at the repo root).

- **Never run the app or `manage.py` from it** — `db` publishes no host port, so anything
  touching the database fails to connect. Use `docker compose exec api …`.
- **After changing `requirements.txt`**, refresh both: `docker compose build api` *and*
  `.venv/bin/pip install -r backend/requirements.txt`.

It sits at the repo root rather than `backend/.venv` because the Dockerfile's `COPY . .` runs
from the `backend/` build context and would bake the venv into the image.

## Lint and tests

ruff is configured in `backend/pyproject.toml` (`select = E W F I UP B DJ`, single quotes, 100
cols); the hook runs `ruff check --fix` + `ruff format` on every edited `.py`. Tests are
`pytest` + `pytest-django` in `backend/tests/`, run inside the container. The `checker` agent
runs ruff, the suite and `makemigrations --check` when `backend/` changed.

## Before committing

`checker`, then `docs` to sync `docs/backend.md` § Decision log and the roadmap § Status, then
hand off to `git`.
