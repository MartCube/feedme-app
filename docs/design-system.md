# Design System

The fixed visual vocabulary every component speaks. It exists so themes are data, not
redesigns: components name *roles* (`bg-elevated`, `text-muted`, `text-title`), and each
theme decides what those roles look like.

The two rules:

> **9 color roles, 4 text sizes.** If you need something outside them, that's a design
> discussion, not a new class. (One standing exception: `text-logo`, the wordmark's own
> size — see § Type scale.)

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
| `border` | `border-default` | Translucent hairline: input outlines, focus rings, dividers. |
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

### Hover state (desktop)

A hovered list row (desktop pointers only) lights its **label** `primary` — and nothing else
moves. No surface step, no wash: `bg-muted` reads *brighter* than `bg-elevated` in both themes,
so stepping a hover to `bg-muted` would make a hovered row louder than a selected one, and a
10% `primary` wash (the first attempt) barely registered — there is no alpha of the accent
that is both visible over `bg-default` and quieter than `bg-elevated`, so it landed as haze.
Colour borrows no surface, which is also why it can **stack** on a row that already has one
(the selected row, or every top-level row in cards mode) instead of having to be withheld
from exactly the rows that most needed feedback. Meta that sets its own colour (counts, the
`text-muted` caption) keeps it, so only the name lights up; a muted feed is dimmed by opacity
rather than `text-muted` for the same reason; an icon that sets its own colour follows by the
same gate (`group-hover`), or the label would light beside a muted icon. The `hover-accent`
utility (`app/assets/css/themes.css`) carries this, wrapped in `@media (hover: hover)` so touch
pointers — where `:hover` sticks after a tap — get nothing. Used across the feed list, the
sidebar's Add feed/Settings entries, settings' section rows, and the edit-folder member rows.

**Selected** is the same cue made to stand: the row's label goes `primary` *and* the row takes
`bg-elevated` + `shadow-elevated` — the tap flash on the way out on mobile, the persistent
master–detail selection on desktop. The name carries the selection rather than the surface
alone because in cards mode every top-level row already has a surface.

### Separation

Two ways to separate content, in order of preference:

1. **Spacing** — the default. Reach for a gap from the six-step scale first; most groupings
   read correctly without any line.
2. **A hairline divider** (`border-default`) — when spacing alone doesn't carry the
   grouping: long uniform lists where rows blur together, or a boundary that must survive
   a tight layout.

**Don't stack both.** A divider *plus* a generous gap *plus* a card edge is three signals
doing one job — pick one and let it work. The same goes for gloss: elevated controls use
`shadow-elevated`, never a translucent ring or inner highlight.

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

**One standing exception: `text-logo`** (2rem, weight 600, line-height 1.1, defined alongside
the scale in `app/assets/css/typography.css`) is the FEEDME wordmark's size and nothing
else's — a logo is a mark, not a size app code picks from, so it sits outside the four-size
rule rather than becoming a fifth general-purpose one. It appears in exactly one place: the
top of the shared feed list (`home/FeedList.vue`), currently a stand-in until a designer
supplies a real mark.

## Spacing

Six steps, t-shirt named, defined as `--spacing-*` tokens in
`app/assets/css/spacing.css` (imported by `main.css`) — the same pattern as the type
scale. Each token generates its utilities (`p-sm`, `gap-md`, `mt-lg`, …). All rem so
they scale with the root font-size (a future layout-density setting is one multiplier).
Tailwind's numeric steps (`p-4`, `gap-6`, …) stay available because Nuxt UI needs them
internally, but app code uses only these six names. A new step is a design discussion,
not a new class.

| Step | Size | Utilities | Use for |
|---|---|---|---|
| `2xs` | 0.25rem (4px) | `gap-2xs`, `mt-2xs` | Intra-element stack: title-over-meta, name-over-URL, date-over-title |
| `xs` | 0.5rem (8px) | `gap-xs`, `mt-xs` | Bound pairs: inline label + trailing meta, section-label → its group, note below a group |
| `sm` | 1rem (16px) | `p-sm`, `gap-sm`, `py-sm` | Workhorse: list-row & card padding, icon/back-button → label gap, block-to-block |
| `md` | 1.5rem (24px) | `mt-md` | Heading → first content (screen title _or_ header row), list-container top |
| `lg` | 2rem (32px) | `mt-lg`, `gap-lg` | Screen top/side inset, navbar/top-control → title, gap between stacked page sections |
| `xl` | 3rem (48px) | `pb-xl` | Bottom scroll runway |

**Screen inset is one class:** every page and drawer panel wraps its content in
`page-inset` (defined as an `@utility` in `app/assets/css/spacing.css`): `lg` sides and
top (top clears the navbar / drawer drag-lip), `xl` bottom scroll runway. Never spell
the inset out with raw padding utilities — changing the app-wide shell must stay a
one-line edit.

Canonical value per recurring slot — reach for these before inventing spacing:

| Slot | Value |
|---|---|
| Screen wrapper inset | `page-inset` |
| Navbar / top-control → title | `mt-lg` |
| Heading → first content / list-container top | `mt-md` |
| List-row vertical padding | `py-sm` |
| Card padding | `p-sm` |
| Icon/back-button + label gap (incl. header rows) | `gap-sm` |
| Inline label + trailing meta gap | `gap-xs` |
| Intra-element stack gap | `gap-2xs` |
| Section-label → group / note below group | `mt-xs` |
| Between page sections | `gap-lg` |

## Layout (desktop shell)

Desktop (≥1024px) presents feeds/posts/settings as a three-column shell instead of the mobile
single-pane stack — see [screens-and-flows.md](./screens-and-flows.md) for the screens this
composes. Its measures are container tokens, not spacing steps, so they never collide with the
six-name `--spacing-*` rule above: defined as `--container-*` in `app/assets/css/layout.css`
(a `@theme static` block, imported by `main.css`).

| Token | Size | Use for |
|---|---|---|
| `--container-sidebar` | 18rem | Sidebar column: the feed list plus the standing Add feed / Settings rows |
| `--container-postlist` | 24rem | Posts (master) pane |
| `--container-reading` | 42rem | Post content measure cap; also the width of the desktop content area's single-pane screens (`/add` — the wizard is linear steps with no list beside them). Settings and edit split the area into two equal panes instead — each the posts pane's 40%, the last fifth left empty, since a form has a natural width and doesn't get better wider the way an article does |
| `--container-post` | 56rem | Post body measure — only bites on wide monitors |
| `--container-signin` | `calc(400px + 2 * var(--spacing-lg))` | The sign-in column on `/login` — the only measure here that isn't a shell one. It is Google's 400px button cap plus the two page-insets, because that button's width can't be raised and a wider column would leave it short of the field below it (see [screens-and-flows.md](./screens-and-flows.md) § 0) |

**Breakpoint:** a single tier at `lg` (1024px, Tailwind's `lg:` prefix) splits mobile from
desktop — below it the app is the mobile single-pane stack, at or above it the three-column
shell. There is no middle tablet tier today. Note the naming collision this introduces: `lg` is
both a *breakpoint prefix* (`lg:hidden`) and a *spacing step* (`gap-lg`) — they mean different
things depending on which utility they prefix, so read `lg:` classes as breakpoints and bare
`-lg` suffixes as the spacing token.

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
