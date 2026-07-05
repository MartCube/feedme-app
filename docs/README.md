# FeedMe Documentation

FeedMe is a **mobile-first, dark-mode RSS / feed reader** — a single, calm place to follow
content from YouTube channels, subreddits, and websites/blogs without the algorithmic noise
of native apps.

These docs are the **product source of truth**. They describe what the app *is* and what a
user can *do* in it. We agree on the spec here first, then build the code to match. When a
screen or feature is ambiguous in code, this folder wins.

## Index

| Doc | What it covers |
| --- | --- |
| [product-overview.md](./product-overview.md) | Vision, target user, and design principles |
| [user-stories.md](./user-stories.md) | What a user can do, grouped by feature area |
| [screens-and-flows.md](./screens-and-flows.md) | Every screen, its purpose, and how navigation connects them |
| [data-model.md](./data-model.md) | The `Feed`, `Folder`, and `Post` entities and the saved-posts state |
| [design-system.md](./design-system.md) | The visual vocabulary — 9 color roles, 4 text sizes, the two themes, and how switching works |
| [current-state.md](./current-state.md) | What's built today vs. not-yet-built (the gap to close) |

## Tech stack (at a glance)

- **Nuxt 4** (`app/` srcDir convention) + **Vue 3** + **vue-router**
- **Nuxt UI 4** + **Tailwind v4** for UI; dark mode is forced on
- **Pinia** for state (`feeds` and `settings` stores)
- **VeeValidate + Zod** for forms/validation (installed, not yet used)
- **@formkit/auto-animate** + **@vueuse/motion** for animation
- **pnpm** package manager; **ESLint** (`@nuxt/eslint`, stylistic)

See [current-state.md](./current-state.md) for what is actually wired up.

## How to use these docs when building

1. Pick a screen from [screens-and-flows.md](./screens-and-flows.md).
2. Confirm the data it needs against [data-model.md](./data-model.md).
3. Check it satisfies the relevant stories in [user-stories.md](./user-stories.md).
4. Keep the [design principles](./product-overview.md) — mobile-first, dark, minimal.
