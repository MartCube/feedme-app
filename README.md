# FeedMe

A quiet, personal feed reader — Reeder-inspired and distraction-free.

Most feed readers fight for your attention: "most popular," trending tabs, recommendation
feeds, and an endless social layer of likes and comments. FeedMe rejects all of it. You add
your own sources and read them in a clean, mobile-first UI — no suggestions, no reactions, no
engagement machinery. Just the sources **you** chose, presented for reading.

A source can be a **YouTube** channel, a **subreddit**, or a **website / blog** (generic RSS).
Each is pulled via its RSS endpoint and presented as a simple, scrollable list you can read,
save, and open at the original source.

## Status

Frontend-only phase. The app runs entirely on static mock data (`app/assets/data.ts`) — RSS
fetching and persistence are not wired up yet.

- **Now** — mobile-first UI, dark mode only, master/detail layout on wide viewports.
- **Planned** — a Django backend for live RSS + persistence, native iOS / Android via
  Capacitor (one shared web core), and optional light theme.

## Tech stack

- **Nuxt 4** (Vue 3 + TypeScript), source in `app/`
- **@nuxt/ui v4** — bundles Tailwind v4, `@nuxt/icon`, `@nuxt/fonts`, `@nuxt/color-mode`
- **Pinia** (+ persisted state) for stores
- **VeeValidate + Zod** for forms
- **pnpm** package manager

## Getting started

Install dependencies and start the dev server on `http://localhost:3000`:

```bash
pnpm install
pnpm dev
```

To test on a phone, run the server exposed to your local network — it prints a QR code you can
scan from any device on the same Wi-Fi:

```bash
pnpm dev:mobile
```

## Scripts

| Command           | What it does                                  |
| ----------------- | --------------------------------------------- |
| `pnpm dev`        | Dev server with HMR                           |
| `pnpm dev:mobile` | Dev server exposed to LAN, with QR code       |
| `pnpm build`      | Production build                              |
| `pnpm preview`    | Preview the production build locally          |
| `pnpm generate`   | Static generation                            |
| `pnpm lint:fix`   | Lint and auto-fix (2-space, single quotes, no semicolons) |
| `pnpm typecheck`  | Type-check with `vue-tsc`                      |

## Documentation

The product spec lives in [`docs/`](./docs):

- [`product-overview.md`](./docs/product-overview.md) — what FeedMe is, who it's for, principles
- [`current-state.md`](./docs/current-state.md) — what's built today
- [`design-system.md`](./docs/design-system.md) — tokens, surfaces, and visual treatments
- [`screens-and-flows.md`](./docs/screens-and-flows.md) — screens, navigation, layout behavior
- [`data-model.md`](./docs/data-model.md) · [`user-stories.md`](./docs/user-stories.md)
