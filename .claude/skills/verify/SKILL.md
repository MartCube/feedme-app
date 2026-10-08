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

## Drive (chrome-devtools MCP)

The `chrome-devtools` MCP server (`.mcp.json`, project scope) drives system Chrome —
headless, isolated profile, 390×844 mobile viewport already configured. No puppeteer
bootstrap, no scratchpad install.

Tools you'll use: `navigate_page`, `click`, `fill`, `take_screenshot`, `take_snapshot`,
`list_console_messages`, `evaluate_script`, `resize_page`.

**Prefer `take_snapshot` over screenshots for finding things.** It returns the a11y tree
with a `uid` per element; `click` takes that uid. This sidesteps the selector-through-the-
overlay trap below entirely — the snapshot tells you what's actually hittable.

Screenshots are for *judging pixels*, not locating elements.

**Desktop shell:** `resize_page` to 1280×800 to cross the `lg` breakpoint into the
three-column layout. Reset to 390×844 for mobile checks.

URL-reachable states: `/`, `/feed/:uid`, `/settings`, `/settings/:panel`, `/add`
(drawers open from the URL; the home page stays mounted behind them).
Wizard steps beyond 1 need real clicks.

## Gotchas (all learned the hard way)

- **The home page stays mounted BEHIND open drawers.** Text/CSS queries will match the
  home page's elements *through* the overlay, and you'll press at coordinates the drawer
  covers. Use `take_snapshot` and click by uid, or scope queries inside `[role="dialog"]`.
- **Never dispatch coordinate-less synthetic PointerEvents inside the drawer** — vaul reads
  `clientY` (0 for synthetic events) as a huge drag, dismisses the sheet, and leaves drag
  state that swallows the NEXT real click. This is why you use the `click` tool rather than
  `evaluate_script` with a synthetic event: `click` sends real input.
- **Capturing the 450ms tap-selection flash** needs a held press — `click` completes too
  fast. Use `evaluate_script` with real `pointerdown` carrying true `clientX`/`clientY`
  from the element's bounding rect, screenshot, then `pointerup`.
- Drawer/panel slides are 350ms — wait ~700-800ms after opening/navigating before
  asserting; ~150ms after a step change to screenshot mid-transition.
- Mock search results always return after ~1s (skeletons first) — wait 1500ms.
- Pinia state is client-side seed data: every full page load resets it.
- Check `list_console_messages` after a flow — Vue hydration warnings surface there and
  nowhere in the pixels.
- **Images: check at a real phone's pixel density, not only the configured 1×.** A srcset
  picks a different file at 3×, and a bug in how it's measured or served stays invisible at
  1×. `emulate` with viewport `390x844x3` (and `1440x900x2` for desktop) before calling
  image work done.

## Useful stable selectors

Snapshot uids are per-session; these `aria-label`s are stable across runs and are what the
snapshot will show you:

- `button[aria-label="Close settings"]`, `button[aria-label="Close add feed"]`
- `a[aria-label="Back to settings"]` (settings subpage), `button[aria-label="Back"]` (wizard)
- Wizard result rows: `ul li button[aria-label="Add feed"]`
- Destination: `button[aria-label="Add to <FeedName>"]`, or the "New feed" row
- Feed page: `button[aria-label="Hide <Source> in this feed"]` / `"Show …"` toggles, `a[aria-label="Edit feed"]`
