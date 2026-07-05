# Design System

The fixed visual vocabulary every component speaks. It exists so themes are data, not
redesigns: components name *roles* (`bg-elevated`, `text-muted`, `text-title`), and each
theme decides what those roles look like.

The two rules:

> **9 color roles, 4 text sizes.** If you need something outside them, that's a design
> discussion, not a new class.

## Color roles

The tokens ride Nuxt UI's semantic CSS variables (`--ui-*`) directly — no custom token
layer, no color ramps — so Nuxt UI components and our own re-color together.

| Token | Utility | Role |
|---|---|---|
| `bg` | `bg-default` | The page. Everything sits on this. |
| `bg-elevated` | `bg-elevated` | One step up: cards, drawers, navbar buttons. |
| `bg-muted` | `bg-muted` | One more step: inputs, hover/pressed states, avatar placeholders. |
| `text` | `text-default` / `text-highlighted` | Titles and body content. |
| `text-muted` | `text-muted` | Secondary info: dates, counts, descriptions. |
| `text-dimmed` | `text-dimmed` | Placeholders and disabled states **only** — never real content. |
| `border` | `border-default` | Translucent hairline: input outlines, focus rings. Lists are divided by spacing, not lines. |
| `primary` | `text-primary`, `bg-primary`, … | Accent: active states, links, key actions. |
| `error` | `text-error`, … | Validation and destructive actions. |

Notes:

- "Lighter/darker" relationships live in the **theme**, not the token. Both launch themes
  elevate by getting lighter; a future light theme elevates by getting darker. Component
  code never encodes direction.
- `border` is translucent (white at low alpha on dark themes) so one value reads correctly
  on any surface and inherits the surface's undertone. Light themes flip it to black at
  low alpha.
- The theme blocks in `themes.css` also set a few Nuxt UI-internal variables
  (`--ui-text-highlighted`, `--ui-text-toned`, `--ui-bg-accented`, …) as **aliases** of
  the roles above, so Nuxt UI internals never render an unmapped color. Aliases are not
  app vocabulary.

**`shadow-elevated`** (the one shadow token) — a soft lift for elevated surfaces: a
same-color 1px edge (the theme's `bg-elevated`) that extends the shape plus a soft drop
shadow — no visible ring or highlight. Icon buttons use it today; cards and drawers can
adopt it as they gain elevation.

## Themes

Two dark themes at launch, switchable in Settings → Appearance:

| Token | Ink (default) | Claude |
|---|---|---|
| `bg` | `#1F1F21` | `#262624` |
| `bg-elevated` | `#252527` | `#30302E` |
| `bg-muted` | `#303032` | `#3A3A38` |
| `text` | `#F2F2F2` | `#F5F4EF` |
| `text-muted` | `#9A9A9E` | `#B8B5A9` (warm "oat") |
| `text-dimmed` | `#6E6E72` | `#83827D` |
| `border` | `rgba(255,255,255,0.07)` | `rgba(255,255,255,0.08)` |
| `primary` | `#2DD4BF` (teal) | `#D97757` (terracotta) |
| `error` | `#F87171` | `#E5695E` |

## Type scale

Four named sizes, defined in the Tailwind theme so they exist as real utilities. All rem
so a future font-size setting is a single root multiplier. **Two weights only: 400
and 600** — only those two Sora weights are loaded.

| Utility | Size | Weight | Line-height | Used for |
|---|---|---|---|---|
| `text-title` | 24px (1.5rem) | 600 | 1.25 | Screen titles, post title on post page |
| `text-subtitle` | 18px (1.125rem) | 600 | 1.35 | Section headers, card/post titles in lists |
| `text-body` | 16px (1rem) | 400 | 1.6 | Reading text, list rows, buttons |
| `text-caption` | 12px (0.75rem) | 400 | 1.4 | Dates, meta, labels — usually with `text-muted` |

Tailwind's stock sizes remain available (Nuxt UI needs them internally), but app code uses
only these four names.

## How theming works

Each theme is a small block in `app/assets/css/themes.css` (imported by `main.css`)
assigning the `--ui-*` variables: `:root, .dark` carries Ink (the default), and
`html[data-theme='claude']` overrides for Claude. The active theme lives in the `settings`
Pinia store (`app/stores/settings.ts`), persisted to a cookie via
`pinia-plugin-persistedstate` (its Nuxt default — cookies let the server render the chosen
theme, so a reload doesn't flash Ink); the same file exports the `themes` list. `app.vue`
applies the store's value as the `data-theme` attribute on `<html>` via `useHead`, so a
theme change re-colors everything reactively and a new theme is just another CSS block plus
an entry in the `themes` list.

## Later (explicitly out of scope for now)

- **Light themes** — the system supports them (elevation flips darker, the hairline flips
  to black at low alpha); none shipped yet.
- **User font-size setting** — the rem scale and the `settings` store are shaped for it.
- **User layout settings** — same home: the `settings` store.
