# Backend init — open questions & deferred decisions

From the hello-world session (2026-08-05). Discuss when back, then delete resolved items.

## Questions

1. **Python dependency tooling** — went with plain `requirements.txt` + pip in Docker
   (least machinery). Fine long-term, or do you want `pyproject.toml` + uv?
2. **Admin superuser** — admin serves at `/admin/` but no account exists yet. Create one
   together (interactive `createsuperuser`), or env-driven?
3. **CORS** — the Nuxt dev server (localhost:3000) will need CORS headers to call the api
   (localhost:8000). Plan: add `django-cors-headers` when we wire the first real frontend
   call — or should the Nuxt side proxy `/api` instead (no CORS at all)?
4. **Committing** — nothing committed. The working tree also has uncommitted *frontend*
   changes from a previous session (scrollbars etc.); want those committed separately first?

## Deliberate deferrals (not questions, just recorded)

- `worker` / `scheduler` compose services wait for the Dramatiq session — a worker with no
  actors module just crash-loops. `redis` is already up and idle for them.
- No auth guard on the API yet — would block hello-world testing; comes with the auth session.
- `db`/`redis` ports are not published to the host (only `api` on 8000). Add a port mapping
  if you want host `psql` access.
- Session order suggestion for next steps: models + admin + migrations → auth (Google +
  bearer tokens) → read endpoints (`/home`, posts) → fetching pipeline (Dramatiq + worker/
  scheduler services) → discovery/search/extraction → frontend wiring + OpenAPI type gen.
