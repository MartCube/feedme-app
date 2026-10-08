# Design System

The fixed visual vocabulary every component speaks. It exists so themes are data, not
redesigns: components name *roles* (`bg-elevated`, `text-muted`, `text-title`), and each
theme decides what those roles look like.

The two rules:

> **9 color roles, 4 text sizes.** If you need something outside them, that's a design
> discussion, not a new class. (Standing exceptions: `text-logo`, the wordmark's own
> size — see § Type scale — and `bg-sunken`, the desktop sidebar's surface — see § Color
> roles.)

## Color roles

The tokens ride Nuxt UI's semantic CSS variables (`--ui-*`) directly — no custom token
layer, no color ramps — so Nuxt UI components and our own re-color together.

| Token | Utility | Role |
|---|---|---|
| `bg` | `bg-default` | The page. Everything sits on this. |
| `bg-elevated` | `bg-elevated` | One step up: cards, drawers, navbar buttons. |
| `bg-muted` | `bg-muted` | One more step: inputs, a post card's selected and hovered surface, pressed states, avatar placeholders. |
| `text` | `text-default` / `text-highlighted` | Titles and body content. |
| `text-muted` | `text-muted` | Secondary info: dates, counts, descriptions. |
| `text-dimmed` | `text-dimmed` | Placeholders and disabled states **only** — never real content. |
| `border` | `border-default` | Translucent hairline: input outlines, focus rings, dividers. |
| `primary` | `text-primary`, `bg-primary`, … | Accent: active states, links (a post's feed name is one, always underlined), key actions. |
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
- **One standing exception: `bg-sunken`** (`--ui-bg-sunken`, utility `bg-sunken`) — a surface
  one step *below* `bg`, themed in `themes.css` alongside the 9 roles above but not one of
  them, since Nuxt UI has no semantic slot for it and defines no built-in class — ours is a
  hand-written `@utility`. Used in exactly one place: the desktop sidebar, which is what
  separates it from the reading panes beside it without a divider line.

**`shadow-elevated`** (the one shadow token) — a soft lift for elevated surfaces: a
same-color 1px edge (the theme's `bg-elevated`) that extends the shape plus a soft drop
shadow — no visible ring or highlight. Icon buttons use it today; cards and drawers can
adopt it as they gain elevation. It belongs on `bg-elevated` surfaces only: the edge is drawn
in `bg-elevated`, so on a `bg-muted` surface (a selected or hovered post card) it would read as
a darker outline instead of extending the shape — those take no shadow.

### Hover state (desktop)

A hovered list row (desktop pointers only) lights its **label** `primary` — and nothing else
moves (the post card is the one carve-out, below). No surface step, no wash: `bg-muted` reads *brighter* than `bg-elevated` in both themes,
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

The same cue reaches standalone icons that have no row label to carry it: every `IconButton`
(`app/components/ui/IconButton.vue`) and the folder/Saved expand chevrons
(`home/FeedList.vue`) light the icon itself `primary` on hover, gated the same way
(`@media (hover: hover)`, via `group-hover/icon` rather than `hover-accent`, since there's no
label doing the work).

**The post card is the carve-out from "label only."** Unlike a list row, a card already rests
on a surface (`bg-elevated`), so stepping that surface is the cue that reads: on hover it goes
to `bg-muted` — the selected surface, so **hovered equals selected, on purpose** — with no
shadow (see `shadow-elevated` above). The `hover-lift` utility (`app/assets/css/themes.css`)
carries it, wrapped in `@media (hover: hover)` like `hover-accent`, and a selected card, already
on `bg-muted`, doesn't take it.

**Selected** is the same cue made to stand: the row's label goes `primary` *and* the row takes
`bg-elevated` + `shadow-elevated` — the tap flash on the way out on mobile, the persistent
master–detail selection on desktop. The name carries the selection rather than the surface
alone because in cards mode every top-level row already has a surface. A post card selects the
other way round: it rests on `bg-elevated`, so selected steps up to `bg-muted` with no shadow
and no label change.

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
| `2xs` | 0.25rem (4px) | `gap-2xs`, `mt-2xs` | Intra-element stack: card meta-over-title, post title-over-meta, name-over-URL |
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
| Post title → its meta row | `mt-2xs` |
| Post meta row → image or video → body | `mt-md` |
| Section-label → group / note below group | `mt-xs` |
| Between page sections | `gap-lg` |
| Desktop sticky pane-top row → its content | the row ends in `pb-sm`; the content takes the remainder so the total matches mobile: `lg:mt-xs` under the posts list's title/search row (sm + xs = `md`), `lg:mt-sm` under the post pane's action strip (sm + sm = `lg`) |

A sticky pane-top row ends in `sm` of its own so content never scrolls flush against its
buttons; the content below gives that `sm` back rather than stacking on it.

## Motion

Two timings, defined as theme tokens in `app/assets/css/motion.css` (imported by `main.css`) —
the same pattern as spacing and the type scale.

| Timing | Value | Used for |
|---|---|---|
| Feedback | 300ms, ease-out | Every colour or surface change: hover, selection, the tap flash, the toggle thumb, the chevron turn |
| Slide | `--duration-slide` 350ms, `--ease-slide` (iOS's curve, `cubic-bezier(0.32, 0.72, 0, 1)`) | Page and drawer-panel slides — mobile only |

Feedback is Tailwind's own transition default (`--default-transition-duration` and
`--default-transition-timing-function`), so a bare `transition` or `transition-colors` gets it —
and so does every Nuxt UI component, which is the point: one feel across the app. Slides read
the two `--*-slide` variables directly (`transitions.css`, `app/utils/panel-slide.ts`).

**App code never writes `duration-*` or `ease-*`.** Timing comes from `motion.css`; a
component that wants a transition says `transition-colors` and nothing more. A new timing is a
design discussion, like a new spacing step. Nothing slides on desktop
([current-state.md](./current-state.md) § Resolved decisions → Desktop motion).

## Layout (desktop shell)

Desktop (≥1024px) presents feeds/posts/settings as a three-column shell instead of the mobile
single-pane stack — see [screens-and-flows.md](./screens-and-flows.md) for the screens this
composes. Its measures are container tokens, not spacing steps, so they never collide with the
six-name `--spacing-*` rule above: defined as `--container-*` in `app/assets/css/layout.css`
(a `@theme static` block, imported by `main.css`).

| Token | Size | Use for |
|---|---|---|
| `--container-sidebar` | 18rem | Sidebar column: the feed list plus the standing Add feed / Settings rows |
| `--container-postlist` | 24rem | Posts (master) pane's empty-state measure only — the pane itself takes 40, 50 or 60% of the area right of the sidebar, per the *Reading panes* setting (default 50) |
| `--container-reading` | 42rem | Post content measure cap; also the width of the desktop content area's single-pane screens (`/add` — the wizard is linear steps with no list beside them). Settings and edit split the area into two equal panes instead — each 40% of the area, the last fifth left empty, since a form has a natural width and doesn't get better wider the way an article does |
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
