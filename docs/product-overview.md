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

FeedMe is a personal **feed reader**. It aggregates the sources a user follows into one
clean, mobile-first reading experience. A source can be:

- a **YouTube** channel,
- a **subreddit** (Reddit), or
- a **website / blog** (generic RSS).

Each source is pulled via its RSS endpoint, and its latest items are presented as a simple,
scrollable list the user can read, save, and open at the original source.

The user arranges sources into **feeds**: a feed is a named group of one source or several,
with a description, read as one merged stream. One source can sit in several feeds, and can be
switched off inside any of them. There are no folders — a feed is already the group.

## Who it's for

People who follow content across several platforms and want **one quiet place** to read it
— without recommendation feeds, autoplay, or notifications competing for attention. The
mental model is closer to an email inbox or a reading app (Reeder) than a social app.

Two products inspire it: **Reeder** for the calm, typography-first reading experience, and
**[crowdfeed](https://crowdfeed.com)** — the author's earlier aggregator, still live — for how
an aggregator presents posts from many platforms side by side, and for the infrastructure
baseline (images, media domain, CDN — see [images.md](./images.md)).

## Platforms & layout

FeedMe is built mobile-first today, but it targets **multiple platforms**: a web app, a desktop
app, and native **iOS / Android** via **Capacitor** (the web build is the shared core). Mobile
is the current focus; the rest come later, off one codebase.

Layout follows the **viewport**, not the platform:

- **Mobile** (< 1024px) — one pane at a time. Tap a feed → its posts; tap the info icon beside
  their title → the feed's own page (its sources, switched on or off right there); tap a post → the post;
  Settings and Add open as bottom drawers.
- **Desktop / wide** (≥ 1024px) — **three columns**: a persistent sidebar (the feed list, plus
  standing Add feed / Settings links, always visible), a posts pane, and a post pane — which
  shows the feed's own page until a post is opened. Settings and Add open inside the post
  pane instead of drawers, beside the posts list; the sidebar stays interactive alongside them.

This is why content uses **nested routes** (post under feed, subpage under settings): the route
encodes the navigation context. The routes themselves don't change between viewports — only how
the layout composes them does: mobile renders one route's page at a time; desktop composes the
sidebar, posts pane, and post pane directly from the route and the app's stores, without a
separate desktop route tree. See [screens-and-flows.md](./screens-and-flows.md).

## Design principles

These are non-negotiable constraints that every screen should honor:

- **Minimal, functional, scalable.** Ship the smallest thing that does the job well, and build
  it so it can grow without a rewrite. Prefer fewer, clearer options over configurability.
- **Mobile-first, responsive.** Designed phone-width-first (`layouts/default.vue` centers a
  narrow column), then expanded — on desktop the same screens open into a persistent sidebar
  plus posts/post panes rather than staying a single centered column. See
  [Platforms & layout](#platforms--layout).
- **Dark themes only — for now.** Enforced in `nuxt.config.ts` (`colorMode.preference: 'dark'`).
  Five dark themes ship, switchable in Settings → Appearance; there is no light theme and no
  light/dark toggle. Light themes are a deliberate *future* step (see
  [Planned](#planned-not-now)).
- **Reeder-style minimalism.** Typography and whitespace carry the design. The full visual
  language (type scale, colors, surfaces, controls) lives in
  [design-system.md](./design-system.md).
- **Overlay secondary actions.** Add feed and Settings layer over the current screen as a
  bottom drawer (`UDrawer`) on mobile, but they're route-backed (`/add`, `/settings/*`), so on
  desktop they open inside the post pane rather than as drawers, beside the posts list. Editing a feed is not an overlay: a feed's page is a screen in the reader flow,
  reached by the info icon beside its title.

## Theme tokens (reference)

Every token — the 9 color roles per theme, the type and spacing scales, the font (Sora) — is
defined in [design-system.md](./design-system.md), which is the authoritative reference. The CSS
lives in `app/assets/css/` (`themes.css` for the themes).

## What FeedMe is *not* (for now)

- Not a social app — no comments, likes, reactions, or posting back to sources.
- Not an engagement machine — no "popular," "trending," or "hot news" surfaces, and no
  algorithmic recommendations. You see your sources, nothing else.
- Not light-themed *yet* — dark themes only for now (see [Planned](#planned-not-now)).
- Not a *push* reader — sources are polled on a schedule (about every 30 minutes) by the
  backend's own worker; nothing notifies you. See [current-state.md](./current-state.md).

## Planned (not now)

Deliberately deferred so today's build stays minimal. Each is architected to scale, but not
built yet:

- **Light themes** — a light theme alongside the dark ones (the system already supports them;
  see [design-system.md](./design-system.md) § Later). Dark stays the default.
- **Card layout options** — the image / compact PostCard style is now specced
  ([images.md](./images.md) § Rendering, built in T15a); other layout options stay deferred.
