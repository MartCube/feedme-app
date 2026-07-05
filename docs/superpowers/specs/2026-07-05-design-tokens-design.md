# Design Tokens & Theming — Design

_2026-07-05. Status: agreed in brainstorming, pending implementation plan._

## Goal

Replace the ad-hoc "some colors and a font" state with a deliberate, minimal token system:
a fixed vocabulary of color roles and text sizes that every component speaks, so that
themes (two dark themes at launch, light themes and user font-size settings later) are
data, not redesigns.

Guiding rule, as everywhere in FeedMe: **minimal, functional, scalable.**

## Approach

Ride Nuxt UI's semantic CSS variables (`--ui-*`) directly instead of feeding it 11-step
color ramps. The existing teal/ink/silver ramps in `main.css` are deleted; each theme is a
~10-line block assigning the variables below. App components already consume these tokens
(`text-muted`, `bg-elevated`, …), so Nuxt UI components and our own re-color together.

Rejected alternatives:

- **Custom `--fm-*` token layer** — would need a permanent bridge mapping onto `--ui-*`
  for Nuxt UI components to follow themes; two vocabularies for one meaning.
- **Full ramps + `app.config` color switching** — every theme needs 11 shades × several
  ramps when the app provably uses ~9 values.

Known risk, accepted: if a future Nuxt UI component internally requires a ramp step, we
add that single step back. Cheap, additive.

## Token vocabulary

**9 color roles + 1 shadow. Nothing else.** If a design need falls outside them, that is
a design discussion, not a new class.

| Token | Utility | Role |
|---|---|---|
| `bg` | `bg-default` | The page. Everything sits on this. |
| `bg-elevated` | `bg-elevated` | One step up: cards, drawers, navbar buttons. |
| `bg-muted` | `bg-muted` | One more step: inputs, hover/pressed states, avatar placeholders. |
| `text` | `text-default` / `text-highlighted` | Titles and body content. |
| `text-muted` | `text-muted` | Secondary info: dates, counts, descriptions. |
| `text-dimmed` | `text-dimmed` | Placeholders and disabled states **only** — never real content. |
| `border` | `border-default` | Translucent hairline: list dividers, input outlines. |
| `primary` | `text-primary`, `bg-primary`, … | Accent: active states, links, key actions. |
| `error` | `text-error`, … | Validation and destructive actions. |

Notes:

- Nuxt UI splits body text across several variables (`--ui-text`, `--ui-text-highlighted`,
  `--ui-text-toned`). Our `text` role sets `--ui-text` **and** `--ui-text-highlighted` to
  the same value (Nuxt UI headings use highlighted); `--ui-text-toned` aliases to `muted`.
  So internals never render an unmapped color, but the app's mental model stays 3 tiers.
- "Lighter/darker" relationships live in the **theme**, not the token. Both launch themes
  elevate by getting lighter; a future light theme elevates by getting darker. Component
  code never encodes direction.
- `border` is translucent (white at low alpha on dark themes) so one value reads correctly
  on any surface and inherits the surface's undertone — the iOS/Claude "glassy hairline"
  look. Light themes flip it to black at low alpha.
- **`shadow-elevated`** (shadow token): the glass edge for lifted surfaces — 1px hairline
  ring + soft drop shadow + faint top inner highlight. Defined once (using the theme's
  `border` value for the ring), replaces IconButton's hand-rolled shadow. Cards, drawers,
  icon buttons use it; flat-on-page elements (list rows) use hairline dividers instead.

## Launch themes

Two dark themes at launch, switchable in Settings → Appearance. Values below are the
starting point; Claude-theme values are eyeballed from claude.ai dark mode and get
fine-tuned on screen once the switch works.

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

In `main.css`, each theme is a commented block: `:root` carries Ink, and
`html[data-theme='claude']` overrides for Claude. Role comments (like the existing ink
ramp comments) stay with each block.

## Typography

Four named sizes, defined in the Tailwind theme so they exist as real utilities. All rem
so a future font-size setting is a single root multiplier.

| Utility | Size | Weight | Used for |
|---|---|---|---|
| `text-title` | 24px (1.5rem) | semibold | Screen titles, post title on post page |
| `text-subtitle` | 18px (1.125rem) | semibold | Section headers, card/post titles in lists |
| `text-body` | 16px (1rem) | regular | Reading text, list rows, buttons |
| `text-caption` | 12px (0.75rem) | regular | Dates, meta, labels — usually with `text-muted` |

- Each size token carries its line-height: title 1.25, subtitle 1.35, body 1.6,
  caption 1.4.
- **Two weights only: 400 and 600.** Only those two Sora weights are loaded (smaller font
  payload).
- Tailwind's stock sizes remain available (Nuxt UI needs them internally), but app code
  uses only these four names.

## Theme switching

- **`app/stores/settings.ts`** — Pinia store persisted to localStorage via
  `pinia-plugin-persistedstate` (new dependency). Owns `theme: 'ink' | 'claude'`. Future
  appearance settings (font size, layout) live here too — hence `settings`, not `theme`.
- **`app/composables/useTheme.ts`** — the only interface components use: exposes the
  current theme and `setTheme()`, reactively applies `data-theme` on `<html>` via
  `useHead`. The store stays an implementation detail behind it.
- **`app/components/settings/Appearance.vue`** — gets the two-option theme switch (its
  first real content).
- Accepted trade-off: a possible one-frame default-theme flash on hard refresh before
  localStorage is read. Fixable later with an inline script if it bothers us.

## Cleanup landing with this work

- Delete the teal/ink/silver ramps from `main.css`; add the two theme blocks and the four
  type-scale tokens.
- `border-silver-200` (4 uses: `pages/index.vue` ×3, `pages/feed/[uid]/index.vue` ×1) →
  `border-default`.
- IconButton's hand-rolled `shadow-[0_0_0_1px_var(--color-ink-800),…]` → `shadow-elevated`.
- `app.config.ts` separator (`border-black/40` + white highlight) → re-expressed with the
  `border` token / `shadow-elevated` idiom.
- Sweep existing text classes onto the 4-size scale (`text-sm`, `text-xl`, `text-2xl`,
  `text-4xl`, `text-xs`, `text-lg` each map to the nearest slot; judgment calls resolved
  toward the role, not the old pixel value).
- Update `docs/` (this spec is the source; `current-state.md` gets refreshed at session
  end per usual practice) with the two rules: **9 color roles, 4 text sizes.**

## Out of scope (explicitly later)

- Light themes (the system supports them; none shipped now).
- User font-size and layout settings (the store and rem scale are shaped for them).
- Any rethink of Sora or the teal hue for the Ink theme.
