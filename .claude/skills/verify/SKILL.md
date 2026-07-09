---
name: verify
description: Drive the running FeedMe app headlessly and capture screenshots to verify UI changes end-to-end
---

# Verifying FeedMe changes in the running app

No test harness — verification is driving the dev app and looking at pixels.

## Launch

```bash
pnpm dev                    # background; ready when curl -sf localhost:3000 succeeds (~15s)
```

## Drive (headless Chrome via puppeteer-core)

No Playwright in the repo. Install `puppeteer-core` in the session scratchpad
(never in the repo) and use system Chrome:

```js
const browser = await puppeteer.launch({
  executablePath: '/usr/bin/google-chrome',
  headless: 'new',
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
})
await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2 }) // mobile-first
```

URL-reachable states: `/`, `/feed/:uid`, `/settings`, `/settings/:panel`, `/add`
(drawers open from the URL; the home page stays mounted behind them).
Wizard steps beyond 1 need real clicks.

## Gotchas (all learned the hard way)

- **The home page stays mounted BEHIND open drawers.** Bare `page.$('h1')` /
  `byText('li', …)` will match the home page's elements through the overlay and
  你'll press at coordinates the drawer covers. Scope queries to drawer content
  (filter by a class unique to the drawer markup, or query inside
  `[role="dialog"]`).
- **Never dispatch coordinate-less synthetic PointerEvents inside the drawer** —
  vaul reads `clientY` (0 for synthetic events) as a huge drag and dismisses the
  sheet, and it also leaves drag state that swallows the NEXT real click. Use
  real input: `page.mouse.move(cx, cy); page.mouse.down()`.
- **Capturing the 450ms tap-selection flash**: real `mouse.down()`, wait ~120ms,
  screenshot, `mouse.up()`.
- Drawer/panel slides are 350ms — sleep ~700-800ms after opening/navigating
  before asserting; sleep ~150ms after a step change to screenshot mid-transition.
- Mock search results always return after ~1s (skeletons first) — sleep 1500ms.
- Pinia state is client-side seed data: every `page.goto` full-load resets it.

## Useful stable selectors

- `button[aria-label="Close settings"]`, `button[aria-label="Close add feed"]`
- `a[aria-label="Back to settings"]` (settings subpage), `button[aria-label="Back"]` (wizard)
- Wizard result rows: `ul li button[aria-label="Add feed"]`
- Destination plus: `button[aria-label="Add to <FolderName>"]` / `"Add to top level"`
