# Add feed: feed preview + one source per pass. Implementation handoff

Agreed with Martin on 2026-11-09. This is the brief for building it. The mockups are in
`designs/` (open them in a browser). The yellow notes on them are design annotations, not UI.
The whole exploration (three directions, two rejected rounds, and the final row) lives on
the design canvas: https://claude.ai/artifact/DRYNdGer8Pw9P9mrFykNzw (the row titled
"FINAL").

Read with: `../BRIEF.md`, `.claude/design/DESIGN-SHEET.md`, `docs/screens-and-flows.md` § 4.

---

## 0. What changes, in one list

The wizard keeps its four steps (Type → Paste or search → Destination → Name new feed). Inside
that:

1. **Multi-select is removed. One source per pass.** There are no checkmarks and no forward
   arrow on the search step. Tapping a result card picks that one source and goes straight
   to Destination. To put several sources into one feed, the user makes several passes. The
   "pointed at a feed" entry (feed page → Add source) makes that cheap.
2. **The result card is redesigned.** The separate open-in-new-tab icon and the select toggle
   both go. The card shows avatar, full name (wrapping, not truncated), a caption that
   *contains* the site link (styled like the post card's source link), and **one button:
   Preview**.
3. **The feed preview is new.** Preview fetches `GET /discover/posts?feed_url=`. **Only a
   successful fetch that returns posts opens anything.** Loading, error and empty all show on
   the Preview button itself.
   - **Desktop:** the preview opens in the **posts list** (the middle column), titled
     "Veritasium · Preview". The wizard stays in the right pane.
   - **Mobile:** the preview opens as a step inside the drawer, with the same title.
4. **Destination:** the "Adding" list and the "Add to" label are replaced by one title,
   "Add Veritasium to".

Type step and Name-new-feed step: **unchanged** (see `../screens/mobile-1-type.png`,
`../screens/mobile-4-new-feed.png`). The name prefill is now simply the one source's name.

### Docs and spec to update alongside the code

- `docs/screens-and-flows.md` § 4: phase 2 is no longer multi-select. Remove "Multi-select",
  "several sources → one destination per pass", "With several picks the feed is created with
  the first, then the rest are added", and the "Adding" list in phase 3. Add the preview
  (desktop: posts list; mobile: wizard step) and the Preview button states. In "Scope", write
  **one source per pass**.
- `docs/current-state.md`: the T14 entry ("No UI consumes it yet") gets its UI half.
- `useAddFeedWizard()` drops its selection set (`isSelected`, toggling, the picks array) in
  favour of a single `picked` candidate.

---

## 1. Search step: result card

Mockups: `designs/mobile-results.html`, `designs/desktop-preview.html` (right pane).

### Layout (per card)

```
[avatar 40]  Name, text-body, wraps (max 2 lines, then clamp)        [ Preview ]
             [icon] link-text (primary, underlined) · meta (muted)
```

- Card: unchanged surface. `rounded-2xl bg-elevated p-sm shadow-elevated`, `gap-sm`, list
  `gap-sm`.
- **The card itself is the pick target.** Tapping or clicking anywhere on it except the link
  and the Preview button picks the source and advances to Destination. Keep today's
  stretched-button pattern: the card button covers the card, and the link and Preview sit
  above it at `z-10`.
- **Name:** `text-body`. Drop `truncate`. Use `line-clamp-2` instead, which fixes the
  "Veritasium …" rough edge.
- **Caption** (`text-caption text-muted`): the first segment is a link to `site_url` (new tab),
  styled exactly like `FeedPostMeta`'s source link: `text-primary`, `underline
  underline-offset-2`, `hover-darken`, `gap-2xs`, with an icon at `size-4`.
  - YouTube: YouTube type icon + "YouTube", then " · 21.4M subscribers" (+ " · In your feeds").
  - Reddit: Reddit type icon + "r/selfhosted" (from `site_url`'s path), (+ " · In your feeds").
  - Website: `i-ph-arrow-square-out-bold` + `displayUrl(feed_url)` (the feed URL stays the
    link text, because it's what tells two feeds of one site apart), (+ " · In your feeds").
  - If `site_url` is null, render the same text without the link (`text-muted`, no icon).
  - Same icon choice as `PostMeta` (`sourceIcon`): the type icon, or arrow-square-out for a
    website.
- **Preview button:** the same component as the input's **Paste chip** (`UButton
  color="neutral" variant="soft" size="sm"`). Label "Preview".
  `aria-label="Preview {name}"`, and that string is also its desktop tooltip.
- The forward (›) button in the header is **removed**. The header holds close and back only.

### Preview button states

Mockup: `designs/mobile-preview-button-states.html`, `designs/desktop-button-states.html`.

| State | Label | Look | Behaviour |
|---|---|---|---|
| Idle | Preview | neutral soft chip, `text-default` | Click → start fetch → *Loading* |
| Loading | Preview | the chip pulses (`animate-pulse`), label `text-muted`; `aria-busy="true"`, aria-label "Loading preview of {name}" | Not clickable again. The card stays pickable. Nothing else on screen changes. |
| Loaded with posts | — | — | Opens the preview (§ 2). Desktop: the button becomes *Previewing*. |
| Previewing (desktop only) | Previewing | label `text-primary`; the card takes the selected state (shadow-elevated is already on, so only the name label turns `text-primary`) | Click → closes the preview (posts list returns to what it showed before) |
| Error | Couldn't load | label `text-error`, same neutral soft surface (no error-tinted fill) | Tooltip / aria-label: the server's `detail` + " Try again" (e.g. "Couldn't read that feed. Try again"). Click → retry → *Loading*. The card stays pickable. |
| Empty (`[]`) | No posts yet | label `text-muted`, `disabled` | aria-label "{name} has no posts yet". The card stays pickable (an empty feed is real and can be added). |

- **Error covers:** HTTP 422 (`{"detail": "Couldn't read that feed."}`), network failure, and
  a **client timeout of 10 s** (measured responses are 0.2–1.3 s; slow sites take several
  seconds). Use the `detail` when there is one, otherwise "Couldn't load that feed."
- States are **per result** and kept for the life of the result list. A new search clears
  them. Cache a successful response per `feed_url` for the session, so Back → Preview again is
  instant.
- Only one fetch at a time: starting a Preview on another result cancels the in-flight one
  (that button returns to *Idle*).
- The chip's width changes with its label. That's fine: it's right-aligned and the name
  column flexes.

---

## 2. The preview

### Desktop: in the posts list

Mockup: `designs/desktop-preview.html` (loaded), `designs/desktop-button-states.html` (posts
list untouched while loading or failing).

- The **posts pane** (middle column) swaps its content for the preview. Sidebar and wizard
  pane are unchanged. The wizard pane keeps the result list, with the previewed card in
  *Previewing*.
- **Title row** (the pane's existing sticky title row): "Veritasium" `text-title`, then
  " · Preview" in `text-muted` (same element). Trailing icon buttons (`IconButton`, 40px):
  - `+` in `text-primary`, aria "Add {name}": does exactly what clicking the card does (pick
    → Destination).
  - `↗` (`i-ph-arrow-square-out-bold`), aria "Open on YouTube" / "Open on Reddit" /
    "Open {domain}": `site_url` in a new tab.
  - `×`, aria "Close preview": restores the posts list.
- **Status line** under the title: `text-body text-muted`, `mt-xs`.
  - "10 posts · latest 4 days ago": a relative time for the newest `published_at`.
  - No post has a date: "10 posts · no dates in this feed". **Never** invent "just now".
  - Fewer than 10: "3 posts · latest …".
- **Posts:** `FeedPostCard` in a **preview mode**, following the account's `postCardStyle`
  like any feed:
  - `FeedPostMeta` shows the **date only**: no source link (it's all one source), and no date
    when `published_at` is null.
  - No `PostActions` (no Save): preview posts aren't stored.
  - The title link goes to `post_url` with `target="_blank"` (there's no in-app reader for
    unstored posts).
  - Excerpt: the existing `stripHtml` + footer cleanup. **Also drop an excerpt that is only
    "Comments"** (Hacker News's preview summaries are just a link labelled "Comments").
  - No image: text takes the full width (existing behaviour). No summary: the card is
    date + title.
- Pick from the wizard (card click) while previewing: the wizard moves to Destination, and
  the preview **stays** in the posts list beside it until the wizard closes or commits.
- **Commit** (feed chosen): as today, the wizard closes and the feed the source landed in
  opens in the posts list, replacing the preview.
- **Close the wizard (× or Esc) while previewing:** the preview closes with it, and the posts
  list returns to what it showed before.
- **Esc order:** first Esc closes the preview, the next closes the wizard (the top layer
  first, per the brief).

### Mobile: a wizard step

Mockup: `designs/mobile-preview.html`.

- A new step between Search and Destination, entered only once posts have arrived (so it
  has no loading state of its own). It slides like every other step.
- **Header row:** close, back ("Back to results"), and on the right `↗` (`IconButton`, aria
  "Open on YouTube" etc.).
- **Title:** "Veritasium · Preview" (`text-title`, " · Preview" in `text-muted`), `mt-lg`.
- **Status line:** as on desktop, `mt-xs`.
- **Posts:** the same `FeedPostCard` preview mode, list `gap-sm`, `mt-md`.
- **Docked action:** `BlockButton` (primary label) "Add {name}" with a plus icon, docked at
  the bottom of the drawer over a `bg-default` strip (`px-lg pt-sm pb-lg`). The list gets the
  `xl` runway so the last card clears it. Tap → Destination.
- Back → the results, scroll position and button states intact.

### URL

Per the brief, the preview is addressable: `/add?type=youtube&q=veritasium&preview=<feed_url>`
(URL-encoded). On load with `preview=`, run the search, then fetch the preview. If that
fails, land on the results with that result's button in *Error* or *Empty*. Back / × remove
the param.

---

## 3. Destination step

Mockup: `designs/mobile-destination.html`.

- Title: **"Add {name} to"** (`text-title`, wraps), replacing the "Adding" list and the
  "Add to" label.
- Everything else is unchanged: the New feed card first, then one card per feed with its
  source count. Tapping commits. Refusals show above the list. New feed → Name step.
- Pointed at a feed (feed page → Add source): as today, steps 3–4 are skipped and the commit
  happens from the search step. With one source per pass, tapping a card **commits straight
  into that feed**. The mobile preview's docked button reads "Add to {feed}" in that case, and
  so does the desktop `+` aria-label.

---

## 4. Copy, exact

| Where | Copy |
|---|---|
| Result button | Preview / Couldn't load / No posts yet / Previewing |
| Result button aria | Preview {name} · Loading preview of {name} · {detail} Try again · {name} has no posts yet |
| Caption link (YouTube) | YouTube · {n} subscribers[ · In your feeds] |
| Caption link (Reddit) | r/{name}[ · In your feeds] |
| Caption link (Website) | {displayUrl(feed_url)}[ · In your feeds] |
| Preview title | {name} · Preview |
| Status line | {n} posts · latest {relative} / {n} posts · no dates in this feed |
| Desktop title-row buttons aria | Add {name} · Open on YouTube / Open on Reddit / Open {domain} · Close preview |
| Mobile docked button | Add {name} (pointed at a feed: Add to {feed}) |
| Destination title | Add {name} to |

Names come from the candidate's `name`. Known messy case: a pasted YouTube @handle returns
"Veritasium - YouTube" (see open question 1).

---

## 5. Token mapping

Every value in the mockups maps to an existing token. **No new colours, sizes, spacing steps
or timings.**

| Mockup value | App token / component |
|---|---|
| `--bg` #1F1F21 | `bg-default` |
| `--el` #252527 (cards, icon buttons, block button) | `bg-elevated` |
| `--mu` #303032 (inputs, chips, avatar/thumb placeholders, skeletons) | `bg-muted` |
| `--tx` #F2F2F2 | `text-default` |
| `--tm` #9A9A9E | `text-muted` |
| `--td` #6E6E72 (placeholders) | `text-dimmed` |
| `--bd` rgba(255,255,255,.07) (input outline) | `border-default` |
| `--pr` #2DD4BF (links, Previewing, + icon, New feed, block-button label) | `text-primary` |
| `--er` #F87171 (Couldn't load) | `text-error` |
| `--sh` (edge + soft drop) | `shadow-elevated` |
| 24px / 600 | `text-title` |
| 18px / 600 | `text-subtitle` |
| 16px / 400 | `text-body` |
| 12px / 400 | `text-caption` |
| gap 4 | `gap-2xs` |
| gap 8 | `gap-xs` / `mt-xs` |
| gap 16 (card padding, card → card, icon → label) | `p-sm` / `gap-sm` |
| gap 24 (heading → content) | `mt-md` |
| gap 32 (top controls → title, side inset) | `mt-lg` / `page-inset` |
| bottom runway 48 | `xl` (part of `page-inset`) |
| card radius 16 | `rounded-2xl` |
| thumbnail radius 12, 128 / 160px | `rounded-xl`, existing `PostImage` sizes |
| pill radius | `rounded-full` |
| icon buttons 48 mobile / 40 desktop | `IconButton` (`size-12 lg:size-10`) |
| avatar 40 | `UAvatar` as in today's `SearchStep` |
| Preview chip (h 32, 12px label) | `UButton color="neutral" variant="soft" size="sm"`, the Paste chip |
| docked button (h 56) | `BlockButton` (primary) |
| pulse 1.6s on the loading chip | `animate-pulse` (the skeleton pulse) |
| step slide (mobile) | `--duration-slide` / `--ease-slide`, existing panel slide |
| link hover | `hover-darken` (as `FeedPostMeta`) |
| desktop tooltip | `UTooltip`, bare muted text (house style) |
| drag lip, 24px drawer corner | existing drawer |
| yellow annotation notes | not UI |

---

## 6. Edge cases checklist (real data in `../data/`)

- **The Verge:** happy path, images, short summaries.
- **Veritasium:** every post is a video with a 16:9 thumb, cropped square by `PostImage` as in
  the feed. Summaries are 4,000 characters, so the existing `line-clamp-3` handles it.
- **YouTube search:** five near-identical names. They now wrap (2 lines max), so "Veritasium
  en español" etc. are distinguishable.
- **r/selfhosted:** 3/10 have images, long HTML summaries. The name is the subreddit title, and
  the caption link shows "r/selfhosted", which carries the recognition.
- **Hacker News:** no images, summary "Comments" is dropped, so the cards are date + title.
- **Paul Graham:** no dates at all. The status line says "no dates in this feed" and the
  cards have no date.
- **Error (422):** the button shows Couldn't load. The preview never opens.
- **Empty `[]`:** the button shows No posts yet (disabled). The source stays pickable.

---

## 7. Open questions

1. **Messy names:** should the backend strip " - YouTube" from a pasted channel's name, so the
   card, preview title, destination title and new-feed prefill all read "Veritasium"? This is
   recommended. Until then the UI shows the name as given.
2. **Excerpt rule for Hacker News:** drop only an excerpt that is exactly "Comments" (as
   specced), or any excerpt under ~3 words?
3. **Mobile preview placement:** specced as a wizard step, because on a phone the posts list
   is behind the drawer. If Martin wants the mobile preview to replace the posts page behind
   the drawer instead, the sheet would need to collapse. That's not designed.
4. **Previewing an "In your feeds" source:** allowed as specced. Should its preview link to the
   feed it's already in? Not designed. Left as is.
