# Product Overview

## Why FeedMe?

Most feed readers and platforms fight for your attention: "most popular," "hot right now,"
trending tabs, recommendation feeds, and the endless social layer of reactions, likes, and
comments. FeedMe rejects all of it.

The idea is **personal and minimal**: you log in, add your own sources, and read them in a
clean, quiet UI. No suggestions about what's popular or what's hot. No reactions, likes, or
comments on any post — yours or anyone's. Nothing optimizing for engagement. Just the sources
**you** chose, presented for reading.

## What FeedMe is

FeedMe is a personal **feed reader**. It aggregates a user's subscribed sources into one
clean, mobile-first reading experience. A source can be:

- a **YouTube** channel,
- a **subreddit** (Reddit), or
- a **website / blog** (generic RSS).

Each source is pulled via its RSS endpoint, and its latest items are presented as a simple,
scrollable list the user can read, save, and open at the original source.

## Who it's for

People who follow content across several platforms and want **one quiet place** to read it
— without recommendation feeds, autoplay, or notifications competing for attention. The
mental model is closer to an email inbox or a reading app (Reeder) than a social app.

## Platforms & layout

FeedMe is built mobile-first today, but it targets **multiple platforms**: a web app, a desktop
app, and native **iOS / Android** via **Capacitor** (the web build is the shared core). Mobile
is the current focus; the rest come later, off one codebase.

Layout follows the **viewport**, not the platform:

- **Mobile** — one pane at a time. Tap a feed → its posts; tap a post → the post; Settings opens
  as a drawer.
- **Desktop / wide** — **master/detail, two panes.** The feed list sits on the left and the
  selected post renders on the right; Settings shows its nav beside the open subpage.

This is why content uses **nested routes** (post under feed, subpage under settings): the route
encodes the navigation context, and the same routes render as one pane or two depending on
width — no separate desktop screens. See [screens-and-flows.md](./screens-and-flows.md).

## Design principles

These are non-negotiable constraints that every screen should honor:

- **Minimal, functional, scalable.** Ship the smallest thing that does the job well, and build
  it so it can grow without a rewrite. Prefer fewer, clearer options over configurability.
- **Mobile-first, responsive.** Designed phone-width-first (`layouts/default.vue` centers a
  narrow column), then expanded — on desktop the master/detail screens open into two panes
  rather than staying a single centered column. See [Platforms & layout](#platforms--layout).
- **Dark mode only — for now.** Enforced in `nuxt.config.ts` (`colorMode.preference: 'dark'`).
  Dark is the only theme we ship today; do not add a theme toggle yet. Theming is a deliberate
  *future* step, kept minimal (see [Planned](#planned-not-now)).
- **Reeder-style minimalism.** Typography and whitespace carry the design. The full visual
  language (type scale, colors, surfaces, controls) lives in the design-system page
  `app/pages/design.vue` and the theme tokens in `app/assets/css/main.css`.
- **Overlay secondary actions.** Add feed and Settings layer over the current screen as a
  bottom drawer (`UDrawer`) on mobile, but they're route-backed (`/add`, `/settings/*`), so on
  desktop they present as panels rather than drawers.

## Theme tokens (reference)

Defined in `app/assets/css/main.css` and `app/app.config.ts`:

- **teal** — primary / accent (e.g. the press-flash on `IconButton`)
- **ink** — neutral dark surfaces and backgrounds
- **silver** — borders and separators
- **Sora** — the app font family

For the authoritative, rendered reference of every token and component variant, run the app
and visit the design page, or read `app/pages/design.vue`.

## What FeedMe is *not* (for now)

- Not a social app — no comments, likes, reactions, or posting back to sources.
- Not an engagement machine — no "popular," "trending," or "hot news" surfaces, and no
  algorithmic recommendations. You see your sources, nothing else.
- Not multi-theme *yet* — dark only for now (see [Planned](#planned-not-now)).
- Not (yet) a live reader — RSS fetching and persistence are not implemented; the app
  currently runs on static mock data. See [current-state.md](./current-state.md).

## Planned (not now)

Deliberately deferred so today's build stays minimal. Each is architected to scale, but not
built yet:

- **Theme switching** — a light theme alongside dark. Kept minimal: **1–2 themes max** to
  start, not a theme gallery. Dark stays the default.
- **Card layout options** — e.g. an image / no-image (compact) PostCard style.
