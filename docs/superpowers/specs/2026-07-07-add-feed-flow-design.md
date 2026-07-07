# Add-feed flow — design

**Status:** approved, ready for implementation planning
**Deliverable:** the UI/UX for adding a feed. No backend — a mock search returns fixed results.

## Goal

Let a user subscribe to a new feed through a guided, in-drawer wizard: pick a source type,
paste a link or search, choose from a short list of results, and place the feed on the home
screen (top-level or into a folder). Minimal, functional, scalable — designed so real search,
RSS discovery, and the Reddit connect step can slot in later without reshaping the flow.

## Shape & architecture

An **in-drawer wizard** hosted in the existing `app/components/add/Drawer.vue`. The drawer still
opens on `/add` and routes home on close (that plumbing stays). Three phases, with slide-right
transitions and a back button, all wizard state held in one place.

```
Phase 1 ──▶ Phase 2 ──────────▶ Phase 3 ──▶ commit → close → home updated
pick type   input → results     destination
   ◀── back ─────── back ───────
```

- **In-drawer wizard (not route-backed).** The phase is component state, not a URL. Sliding
  between phases is a Vue/CSS transition. The **back button** steps back through phases;
  dragging the sheet down or the browser back button closes the whole drawer. (Route-backed
  steps were considered and rejected: they spread the flow's state across routes and make each
  throwaway step a history entry.)

## Phase 1 — Pick a type

- Header: **Add feed** + close (✕).
- A vertical list of type rows, each tappable → slides to phase 2:
  - **Website** — "Any site or RSS feed"
  - **YouTube** — "Channels by link or search"
  - **Reddit** — "Subreddits by link or search"
- Podcasts are intentionally omitted for now; the type model leaves room for them.
- Reddit is selectable and behaves like the others in this build (paste/search a subreddit).
  Its future account-connect step slots in front of the Reddit branch — see
  [`pending_tasks/reddit-connect.md`](../../../pending_tasks/reddit-connect.md).

## Phase 2 — Input → results

- Header: **back** (←) + the chosen type as the title (e.g. "YouTube").
- One input, placeholder **"Paste a link or search…"**, submit via enter or a submit icon. The
  input does double duty: paste a link *or* search a keyword.
- **Paste chip:** when the input is empty, a small **Paste** chip shows inside it; tapping it
  reads the clipboard (`navigator.clipboard.readText()`) and fills the input. Browsers restrict
  silent clipboard reads, so this is tap-to-paste (a user gesture), not auto-fill — honest and
  still one tap on mobile.
- **Submit** → a ~1s **skeleton** of 2–3 placeholder rows (reads as content arriving), then
  **results**.
- **Results:** a short list of feed cards, each showing **title + website** and a `+` on the
  right. No leading type icon — the type is already in the header. Tapping `+` on a row →
  phase 3, carrying that one feed.

## Phase 3 — Choose destination

- Header: **back** (←) + "Add to".
- The home feed list, reused as a destination picker:
  - a **Feeds (top level)** row on top (adds the feed loose),
  - then each **folder** row (name + feed count).
- **Tap a destination → commit.** One tap adds the feed there and closes the drawer; the home
  screen reflects it immediately.

### Scope: one feed → one destination

This build adds **one feed to one destination** at a time. Multi-feed select (grab several
results at once) and multi-destination (one feed in several folders) are deferred. This costs no
flexibility: the data model is already many-to-many, and a feed can be added to more folders
later via a folder's **Edit feeds** action (see `docs/screens-and-flows.md`, screen 7).

## The mock

A `mockSearch(type, query)` that **ignores the query** and returns a **fixed, per-type** short
list after a ~1s delay — YouTube → channels, Website → sites, Reddit → subreddits — so it feels
real while always returning the same result. Lives alongside the existing mock data
(`app/assets/`).

## State & store changes

- **Wizard state** in a small composable `useAddFeedWizard()`:
  - state: `step` (`'type' | 'input' | 'destination'`), `type`, `query`, `loading`, `results`,
    `selectedFeed`.
  - actions: `selectType`, `search`, `pickFeed`, `chooseDestination`, `back`, `reset`.
  - `reset` runs when the drawer closes. Keeps `Drawer.vue` thin.
- **Store:** add `addFeed(feed, destination)` to `useFeedsStore`:
  - pushes the feed into `feeds`,
  - if `destination` is a folder uid, appends the feed's uid to that folder's `feed_uids`,
  - the new feed gets a generated `uid` (`feed_*` prefix, per the data model).

## Component boundaries

- `add/Drawer.vue` — host: `UDrawer` + step switch + slide transition + open/close routing
  (existing).
- `add/TypeStep.vue` — the type list; emits `select(type)`.
- `add/SearchStep.vue` — header (back + type), input + paste chip, loading skeleton, results
  list; emits `back`, `pick(feed)`.
- `add/DestinationStep.vue` — destination list (top-level + folders); emits `back`,
  `choose(destination)`.
- Slide transition classes live in `app/assets/css/main.css` (no `<style>` blocks in
  components, per house style).

## Out of scope (later)

- Multi-feed select and multi-destination placement.
- Reddit account-connect UI (`pending_tasks/reddit-connect.md`).
- Real search, RSS discovery, and live feed metadata (sub counts, latest items).
- Form validation via the installed VeeValidate + Zod stack.
- Richer result cards (thumbnails, counts, descriptions).

## Docs to update at implementation time

- `docs/screens-and-flows.md` screen 4 — replace the "visual demonstration only" note with the
  wizard flow.
- `docs/current-state.md` — reflect the add flow shipping.
