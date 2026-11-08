# FeedMe: Add feed + feed preview, design brief

FeedMe is a calm, distraction-free news reader inspired by Reeder. Minimalism is the product.
Mobile first (it will ship as a Capacitor app), with a three-column desktop shell from 1024px.
Dark themes only, for now.

**The ask:** rework the **Add feed** flow and design the new **feed preview**: a candidate's
latest posts, shown *before* the user adds it, so they can answer "is this feed alive, and is it
about what I think?" inside the wizard instead of adding it, reading it and removing it.

Read `../DESIGN-SHEET.md` (`.claude/design/DESIGN-SHEET.md`) for the visual rules; the full spec is `docs/design-system.md` and `docs/screens-and-flows.md` § 4. `screens/` shows the flow as built today and
`data/` holds real API responses for the preview to be designed against.

---

## 1. The flow today (see `screens/`)

On mobile it's a bottom drawer. On desktop it opens in the right-hand pane and the sidebar and
posts list stay usable beside it. It's a wizard: steps slide left/right on mobile and cut on
desktop. The header row holds close (×), back (‹) and, on the search step, a forward arrow (›).

| Step | Screen | What happens |
|---|---|---|
| 1. Type | `mobile-1-type.png`, `desktop-1-type.png` | Pick **Website**, **YouTube** or **Reddit**. Tapping one advances. |
| 2. Paste or search | `mobile-2a-search-empty.png` → `2b-search-results` → `2c-search-picked`, `desktop-2-search-picked.png` | One input: paste a link *or* type a keyword. While it's empty it shows a **Paste** chip. Results are cards: avatar/icon, name, then the feed URL or subscriber count, an open-in-new-tab icon, and a round **select** toggle. Multi-select. A result already in one of the user's feeds stays pickable and is captioned "In your feeds ·". |
| 3. Destination | `mobile-3-destination.png`, `desktop-3-destination.png` | A quiet "Adding" list of the picks, then **Add to**: a **New feed** card first, then one card per existing feed with its source count. Tapping a feed commits and the drawer closes. |
| 4. Name new feed | `mobile-4-new-feed.png` | Name input, prefilled with the first pick's name. Submit creates the feed. |

The wizard can also open **pointed at a feed** (from a feed's page → "Add source"). Then it
skips steps 3–4 and commits straight from step 2.

`reference-mobile-feed-post-cards.png` is the app's real post card (source link · date, title,
2–3 lines of summary, thumbnail on the right). The preview should speak this same vocabulary
rather than invent a new card.

The screenshots are in the **Crowd** theme (lavender accent). The default theme is **Ink**
(teal). Either is fine to design in. Colors are roles, not hex (see DESIGN-SHEET).

### Known rough edges (free to fix)

- YouTube result names truncate hard on mobile ("Veritasium …"), and those five channels are
  indistinguishable without the full name.
- The select toggle and the open-in-new-tab icon sit side by side on a card that is itself
  the select target. The preview adds a third thing to do with a result, so this row needs a
  rethink, not just one more icon.
- The step-3 "Adding" list is very quiet.
- Keyword search under **Website** and **Reddit** finds nothing yet (it comes later). Only
  pasted links work there, and YouTube supports both links and keywords. The empty and
  no-results states still need to read well.

## 2. What to design

1. **The feed preview**: how a user opens it from a result, what it shows, and how they get
   from it to *picking* that feed (or back to the list). Real data, all the cases in § 3.
2. **The revisited flow** around it: steps 1–4 above. Restructure if the preview suggests a
   better shape (e.g. merging or reordering steps). Keep what works.
3. Both **mobile (390 wide)** and **desktop (the right-hand pane, ~42rem content width,
   sidebar + posts list visible beside it)**.

### Questions worth exploring (not decided; propose answers)

- **Where does the preview live?** Inline expand under the result row, its own wizard step
  (slide in, back returns to the results), or a sheet over the list. Mobile and desktop may
  differ.
- **Picking vs previewing.** Today tapping a card = select. With a preview, what does a tap do,
  and where does the select live? (Multi-select must survive. Several sources can go into one
  feed in a single pass.)
- **What's shown per post.** Title and date at minimum. Image? Summary? The data in § 3 varies
  a lot; the design must hold up when there's no image, no summary or no date.
- **"Is it alive?" at a glance.** E.g. a one-line summary above the posts: "10 posts · latest
  2 days ago" / "No dates in this feed". Design that line if it helps.
- **Can a preview post be opened?** Probably as an external link to `post_url` only (preview
  posts aren't stored, so there's no in-app reader for them).
- **Loading and error states** for the preview (see timing below).

## 3. The preview data (see `data/`)

Endpoint: `GET /discover/posts?feed_url=…` → up to **10 newest posts**, fetched live on every
call and never stored. Each post:

```json
{
  "title": "string",
  "post_url": "string",
  "image": { "src": "url" } | null,
  "video": { "src": "youtube embed url", "vertical": false } | null,
  "summary": "raw feed HTML, may be empty",
  "published_at": "ISO datetime" | null
}
```

Failure: HTTP 422 `{"detail": "Couldn't read that feed."}` (`data/preview-error.json`).
An empty list `[]` is a real answer too: the feed exists but has nothing in it.

**Timing (measured):** 0.2–1.3 s on these feeds. Slow sites can take several seconds. It
needs a loading state. The app already uses pulsing skeletons, not spinners, inside content.

The candidates come from `GET /discover` (each file's `candidate` field): `name`, `type`,
`site_url`, `feed_url`, `icon`, `subscribers` (YouTube keyword search only, else null),
`already_subscribed`.

| File | Feed | What makes it a useful case |
|---|---|---|
| `the-verge.json` | The Verge (website) | The happy path: 10/10 with images, short clean summaries, dated today |
| `veritasium.json` | Veritasium (YouTube, from a pasted @handle) | Every post is a **video** with a 16:9 thumbnail. Summaries are 4,000-character descriptions, so clamp hard. **Name comes back as "Veritasium - YouTube"**: names can be messy |
| `youtube-search.json` | Keyword search "veritasium" | 5 channels with avatars and subscriber counts (21.4M … 38.2K), near-identical names |
| `r-selfhosted.json` | r/selfhosted (Reddit) | **Mixed**: 3/10 with images. Summaries are long HTML with code blocks. The name is the subreddit's title ("Self-Hosted Alternatives to Popular Services"), not "r/selfhosted" |
| `hacker-news.json` | Hacker News (website) | **No images at all**, and the summary is just a "Comments" link. Titles only, in practice |
| `paul-graham.json` | Paul Graham essays (website) | **No dates at all** (`published_at: null` on every post) and empty summaries. The preview must not invent "just now"; it should say plainly that there are no dates |
| `preview-error.json` | A URL that isn't a feed | The 422 error state |

Image URLs in `data/` point at the original hosts so they load in the design tool. In the app
they go through our image proxy, which doesn't change anything visually.

## 4. Constraints

- **Vocabulary:** a **Feed** is the user's named group of sources. A **Source** is one RSS
  endpoint (a site, a channel, a subreddit). A **Post** is one item. In the wizard a "result"
  is a candidate source. There are no folders. Don't introduce new nouns.
- **URL-addressable:** the wizard's type and query will move onto the URL, and an opened
  preview should be addressable too (e.g. `/add?type=youtube&q=veritasium&preview=<feed_url>`).
  Design so a reload or a shared link lands on the same screen.
- **Mobile drawer:** a bottom sheet with a drag lip at the top. Content scrolls inside it.
  Don't fight the drag gesture with horizontal swipes.
- **Desktop:** no slides (steps cut). Hover states exist (see DESIGN-SHEET § Hover). Keyboard:
  Esc closes the top layer.
- **Accessibility:** every icon button has an aria-label that doubles as its desktop tooltip.
  Inputs have labels.
- **Minimal:** no new colors, no new text sizes, no gloss, no stacked separators. If the design
  genuinely needs an exception, call it out explicitly, as the auth designs did with
  `text-hero`.

## 5. What to send back

The same handoff shape as the last round (the auth screens). Export a folder containing:

- `HANDOFF.md`: an implementation brief for Claude Code. Screen by screen: layout, copy, states
  (loading / empty / error / no-dates / no-images), interactions, and what changes in the flow.
- `designs/*.html`: the mockup source per screen, mobile and desktop.
- A **token mapping table**: mockup values → the app tokens in DESIGN-SHEET (e.g. `c.elevated`
  → `bg-elevated`, gap 16 → `gap-sm`). Never raw hex/px without a mapping.
- Any open questions the design couldn't settle.

The folder goes to `.claude/design/add-feed/handoff/` in the repo, where Claude Code
implements it.
