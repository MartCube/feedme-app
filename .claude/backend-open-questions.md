# Backend — open questions & deferred decisions

Updated after the models session (2026-08-07). Discuss, then delete resolved items.

## Questions

1. **CORS vs proxy** — when the Nuxt app makes its first real API call: add
   `django-cors-headers`, or proxy `/api` through the Nuxt dev server (no CORS at all)?
   Decide in the frontend-wiring session.
2. **UserSettings fields** — model currently has the spec's `theme` + `feed_list_style`.
   The frontend settings store has since grown `scrollbarStyle` (and two sidebar-expansion
   flags that feel device-local, not account-level). Decide what syncs to the account when
   building `GET/PUT /settings`.
3. **Subagent models** — the checker/design-reviewer/docs/git agents are configured with
   kimi model ids that this environment can't reach; every launch needed a manual
   haiku/sonnet override. Update `.claude/agents/*.md` frontmatter (and the model-policy
   memory) or restore kimi access.

## For you to do

- Set `DJANGO_SUPERUSER_EMAIL` + `DJANGO_SUPERUSER_PASSWORD` in `.env`, then
  `docker compose restart api` — the entrypoint creates the admin account automatically.

## Deliberate deferrals

- `worker` / `scheduler` compose services wait for the Dramatiq session.
- No auth guard on the API yet — comes with the auth session (next up).
- Post search machinery (generated tsvector, GIN + trigram indexes, pg extensions) waits
  for the search session — additive migrations, per spec § Search.
- Delete-folder cascade (unsubscribe members unless in another folder) is API logic,
  not DB cascade — lands with the endpoints session.
- `db`/`redis` ports not published to host; add a mapping if you want host `psql`.
- Session order: ~~models + admin~~ → **auth (Google + bearer tokens)** → read endpoints
  (`/home`, posts) → fetching pipeline (Dramatiq + worker/scheduler) → discovery/search/
  extraction → frontend wiring + OpenAPI type gen.
