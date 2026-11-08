# FeedMe design sheet (condensed from the app's design system)

The rule: **9 color roles, 4 text sizes, 6 spacing steps.** Anything outside them is a
design discussion and must be called out, never slipped in.

## Color roles

Components name roles; themes decide the values. Design with the roles.

| Role | Utility | Use |
|---|---|---|
| bg | `bg-default` | The page |
| bg-elevated | `bg-elevated` | One step up: cards, drawers, icon buttons |
| bg-muted | `bg-muted` | One more step: inputs, selected/hovered post card, pressed states, image placeholders |
| text | `text-default` | Titles, body |
| text-muted | `text-muted` | Secondary: dates, counts, descriptions |
| text-dimmed | `text-dimmed` | Placeholders and disabled **only**, never real content |
| border | `border-default` | Translucent hairline: input outlines, dividers |
| primary | `text-primary` / `bg-primary` | Accent: active states, links, key actions |
| error | `text-error` | Validation, destructive actions |

Two themes for reference (six ship: Crowd, Blueberry, Ink, Claude, Dracula, Reddit):

| Role | Ink (default) | Crowd (in the screenshots) |
|---|---|---|
| bg | `#1F1F21` | `#141416` |
| bg-elevated | `#252527` | `#1E1E22` |
| bg-muted | `#303032` | `#27272C` |
| text | `#F2F2F2` | `#FFFFFF` |
| text-muted | `#9A9A9E` | `#ADADAE` |
| text-dimmed | `#6E6E72` | `#727276` |
| border | `rgba(255,255,255,0.07)` | `rgba(255,255,255,0.07)` |
| primary | `#2DD4BF` teal | `#A399FF` lavender |
| error | `#F87171` | `#F65B39` |

**One shadow:** `shadow-elevated`, a soft lift for `bg-elevated` surfaces only (a same-color
1px edge + a soft drop shadow, no visible ring). **No gloss**: no translucent rings, no inner
highlights. **`bg-primary` filled buttons are for signed-out screens only.** Inside the app the
full-width action is `bg-elevated` + `shadow-elevated` with a colored label (`text-primary`,
`text-default` or `text-error`).

## Type: Sora, weights 400 and 600 only

| Utility | Size | Weight | Line-height | Use |
|---|---|---|---|---|
| `text-title` | 24px | 600 | 1.25 | Screen titles |
| `text-subtitle` | 18px | 600 | 1.35 | Section headers, card/post titles in lists |
| `text-body` | 16px | 400 | 1.6 | Reading text, list rows, buttons |
| `text-caption` | 12px | 400 | 1.4 | Dates, meta, labels (usually `text-muted`) |

## Spacing: six steps

| Step | px | Use |
|---|---|---|
| `2xs` | 4 | Inside one element: meta over title, name over URL |
| `xs` | 8 | Bound pairs: label + trailing meta, section label → its group |
| `sm` | 16 | The workhorse: card padding, row padding, icon → label, block to block |
| `md` | 24 | Heading → first content |
| `lg` | 32 | Screen side/top inset, top controls → title, between page sections |
| `xl` | 48 | Bottom scroll runway |

Screen inset: `lg` sides and top, `xl` bottom (desktop top is `md`).

## Shapes and sizes

- Cards: `rounded-2xl` (16px), `p-sm`, `bg-elevated`. Images inside: `rounded-xl` (12px).
- Post card thumbnail: square, 128px on mobile (160 / 176px on wider screens), on the right.
  The image box holds its size from first paint and pulses (`bg-muted`, `animate-pulse`) until
  loaded.
- Icon buttons: round, `bg-elevated` + `shadow-elevated`, 48px on mobile / 40px on desktop,
  icon in `text-muted`.
- Icons: **Phosphor** (`ph:`) only, one family app-wide.

## Separation

1. **Spacing first.** Most groupings need no line.
2. **A hairline** (`border-default`) only when spacing can't carry it (long uniform lists).

**Never stack them.** A divider + a big gap + a card edge is three signals doing one job.

## States

- **Hover (desktop only):** a hovered list row lights its **label** `text-primary`, nothing else.
  A post card is the exception: its surface steps `bg-elevated` → `bg-muted`.
- **Selected:** label `text-primary` + `bg-elevated` + `shadow-elevated`.
- **Focus:** one `primary` line on inputs, never two signals.
- **Loading inside content:** skeletons that pulse, not spinners.
- **Links that rest in primary** (the post card's source link) are underlined and darken on hover.

## Motion

Feedback 250ms ease-out (colors). Slides 350ms iOS curve, **mobile only**: desktop cuts. No
other timings.

## Post card anatomy (the vocabulary the preview should reuse)

```
[source icon] Source name (primary, underlined) · 8 Nov 2026   ┌────────┐
Post title, text-subtitle, wraps                               │ thumb  │
Summary, text-body text-muted, clamped to 3 lines              └────────┘
```

Card `bg-elevated rounded-2xl p-sm`, thumbnail on the right, no image → text takes the full width.
