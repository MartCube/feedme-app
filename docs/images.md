# Images

How every image the app shows gets from a third party's server to an `<img>` — post images on
cards and the post page, feed icons, the pictures inside an extracted article, and one day a
user's avatar. Peer to [backend.md](./backend.md) (which owns the tables and endpoints these
ride on); the build order is [backend-roadmap.md](./backend-roadmap.md) T15a–T15e.

_Decided 2026-09-15. **T15a — the proxy, post images, the card toggle — shipped 2026-09-22.
T15c — article images — shipped 2026-09-23. T15b — feed icons — shipped 2026-09-28.** T15d and T15e are still ahead._

## The one rule

**The frontend never builds an image URL.** The API returns ready `<img>` attributes
(`src`, `srcset`) and the app puts them in the tag. On the backend, `core/images.py` is the
**only** module that knows how such a URL is made — a containment test enforces it, the way
`core/search.py` is the only module that queries the search column.

Two reasons. Image URLs are **signed**, and a key on the client is a key in the bundle. And
that one module is the **upgrade seam**: every later stage below — storing originals, a CDN, a
paid resizer — is a change inside it. Components and the API contract never move.

## Why not just hotlink `image_url`

The ingest already stores `Post.image_url` and `Source.icon_url`. Putting those straight in an
`<img>` fails four ways: **hotlink protection** (Reddit and plenty of CDNs refuse a foreign
referer — and `capacitor://localhost`, the planned native build's origin, is the most foreign
referer there is); **mixed content** (an `http://` image on our `https://` page is blocked);
**no size control** (a 4 MB blog hero fetched for a card, ten cards per page); and **privacy**
(every reader's IP and referer goes to every source). It also can't give the card, the post page
and a retina screen the sizes they need — that takes something that resizes.

Measured, not just theorised: the add wizard's YouTube avatars hit hotlink protection directly
_(2026-09-18)_ — Google's image CDN (`yt3.ggpht.com`) throttled five concurrent hotlinked
requests carrying a foreign referer to one success and four 429s.
`referrerpolicy="no-referrer"` was the interim fix on that one `<img>`; T15b replaced it by
serving icons through the proxy.

## Three stages

The shape is staged so the app works really well for its first hundred readers on one server,
and grows by adding pieces rather than replacing them.

| Stage | What runs | What we store | What it fixes | Move on when | Task |
| --- | --- | --- | --- | --- | --- |
| **1. Proxy** | `imgproxy` beside `api` / `worker` in compose | nothing | hotlinking's four failures; sizes; WebP | before real users, or the first "my saved post lost its image" | T15a |
| **2. Bucket** | + the worker copies each new post's original into a bucket (MinIO in dev, R2 / S3 in prod); imgproxy reads from it | originals, deleted with the post | permanence; a truthful `image: null`; dimensions | a deploy target exists | T15d |
| **3. CDN / paid** | + `img.<domain>` in front of imgproxy behind Cloudflare; later a second imgproxy or a paid transformer reading from the bucket | derived images live in the CDN cache | first-view latency; transform CPU | — | T15e |

**Stage 1 — Proxy.** imgproxy is a small, single-binary image server. The API hands the app
a signed URL per size; imgproxy fetches the original from the source, resizes and crops it,
converts to WebP, and answers with a one-year `Cache-Control`. Nothing is stored on our side:
the browser cache holds what a reader has seen, and in production the CDN holds everything
anyone has seen. Costs accepted for this stage, all three paid off by stage 2: an image the
source has deleted is gone (mostly old saved posts); a dead image is discovered at read time
(the box appears, fails to load, and collapses); and the first view of any image depends on a
stranger's server.

**Stage 2 — Bucket.** At the end of a poll the worker copies the originals of the source's new
posts into a bucket — sequentially, one host and one request at a time, so a feed with fifty
new posts is not a burst — and reads each image's dimensions. `core/images.py` points imgproxy
at the bucket copy when one exists, and answers `null` for an image too small to show. Prune
deletes the objects with the posts. This is what crowdfeed had (permanence on S3 behind
CloudFront) with one difference: crowdfeed pre-rendered two JPEG sizes at ingest and so never
gained a third, retina, WebP, or resized avatars — every new size was a backfill over the
whole table. Here the sizes stay recipes and the bucket holds only originals.

**Stage 3 — CDN, then paid.** At deploy, `img.<domain>` points at imgproxy and sits behind
Cloudflare's free tier; a signed URL is deterministic, so the cache hit rate is what it should
be. When transform CPU shows on a graph, run a second imgproxy (it is stateless) or swap the URL
builder to a managed transformer that reads from the bucket (Cloudflare Images Transformations,
Bunny Optimizer). That is every paid image product worth buying: a hosted version of the
proxy model — which is why stage 1 is the shape that upgrades and pre-rendering is not.

At 100 readers, stage 1 is one idle container; stage 2 is that plus roughly $0.50 a month of
bucket; stage 3's CDN is free. Distinct images viewed per day is the number that scales, and
with global sources it grows with the source count, not the reader count.

## What the app shows

| Image | Where the URL comes from | Shown | Recipe | When it can't | Task |
| --- | --- | --- | --- | --- | --- |
| **Post image, card** | `Post.image_url` — ingest's `media:thumbnail` → image enclosure pick | the *image* style of PostCard, a square beside the text | 16:9 fill, widths 480 / 960 / 1440 / 1920, WebP — the box crops it square | the card is *compact* | T15a |
| **Post image, hero** | same | the post page, above the title | same family, `sizes` for the reading measure | no hero | T15a |
| **Feed icon** | `Source.icon_url` — see § Feed icons below | add-wizard rows for every type; other surfaces when the design says so | 64 × 64 fill-down, centre crop (ICO and SVG in) | `UAvatar` initials | T15b |
| **Article images** | `<img src>` inside `article_html` (T10) | the reader | fit to the reading width, no crop, rewritten at read time | dropped from the markup (no key, an unproxiable `src`); a proxy fetch failure at render time is the browser's own broken image | T15c |
| **User avatar** | Google's `picture` claim | Settings → Account | 64 × 64 | initials | T15b, optional |

Not in this pipeline: the app's own icons (PWA, Capacitor) — static assets.

## Wire contract

Stable across all three stages. The database columns (`Post.image_url`, `Source.icon_url`) do
not change; only the wire shape does.

```ts
// Post — replaces image_url on the wire
image: { src: string, srcset: string } | null
//   src    = the 960w URL, a safe default for a bare <img>
//   srcset = "…480w, …960w, …1440w, …1920w" — the attribute, ready
//   null   = the post has no image, or images are off (no IMGPROXY_KEY)

// Feed and FeedCandidate (T15b, shipped) — replaces icon_url on the wire
icon: string | null                   // 64 × 64

// ArticleSchema — article_html arrives with its <img src> already rewritten

// Me (T15b, optional)
avatar: string | null
```

`srcset` travels as the finished string, not as a list of widths: the backend is the one
place that knows which sizes exist, so the two sides cannot disagree about them. The frontend
adds the one thing only it knows — how wide the slot is: `sizes="(min-width: 1024px) 40vw,
100vw"` on a card (the desktop posts pane is 40–60% of the viewport, by the Appearance split), `sizes="(min-width: 1024px)
56rem, 100vw"` on the hero (`--container-post`).

`image_url` is **renamed** to `image` rather than reused with a new meaning, so that `pnpm
types:api` plus typecheck finds every consumer — `PostCard.vue` and `PostView.vue`, as of T15a.

## Sizes and formats

- **One 16:9 family for cards and the hero**, widths 480 / 960 / 1440 / 1920 (heights follow).
  480 covers a 1× phone; 960 a 2× phone and a 1× desktop pane or reading measure; 1440 a 3×
  phone and a 2× pane; 1920 a 2× reading measure. A card is 16:9 on top like crowdfeed's `md`,
  which was 576 × 324 — one size for every screen; this is that idea with retina.
- **Crop is centre, not "smart".** Predictable, and it is what removes YouTube's letterbox: the
  RSS poster is `hqdefault.jpg`, 480 × 360 with 45px black bars top and bottom, and a centred
  16:9 crop takes exactly those off. Most blog heroes are near 16:9 already, so the crop rarely
  bites; smart gravity can be a per-type refinement later.
- **imgproxy never enlarges — measured against a real source, not assumed.** A plain `fill`
  skips the crop entirely when the source is smaller than the requested size, since running it
  would mean enlarging: a real YouTube `hqdefault.jpg` (480 × 360, bars and all) came back
  exactly as fetched, letterbox included. `fill-down` is the fix, used for the whole 16:9 family
  — it shrinks the *requested* size to fit the source instead, so the crop still runs and
  nothing is enlarged. Below 320px wide the app hides the image instead — see Rendering.
- **WebP, named in the URL** (`.webp`), not negotiated from the `Accept` header: one URL is one
  file, so no `Vary` for a CDN to get wrong. AVIF is a later `<picture>` upgrade if bandwidth
  ever matters.
- **Cache for a year.** A signed URL for a given source and size is the same string every
  time, so browser and CDN caches are stable; a key rotation changes every URL and the caches
  simply refill.
- Icons are 64 × 64 (2× of a 32px slot). Article images fit the reading width (1920 at 2×)
  with no crop.

## Rendering

- **A fixed box**, `object-cover`, `rounded-xl`, on a `bg-muted` placeholder — the design system's "avatar placeholders" role. The box is sized before the
  image arrives, so nothing shifts; there are no dimensions to store. The box is **square beside
  the text on a card** _(2026-09-28; was 16:9 on top)_ — 128px, then 160 / 176 / 192 at `md` /
  `lg` / `xl` — cropped from the same 16:9 family; and **16:9 on the post page**, where it
  also takes `noUpscale`: the box is capped at the image's natural width and centred, since a
  640px Reddit preview stretched across a wide pane is a blur.
- A **YouTube post's** image slot on the post page is the player, not a still — see
  [backend.md](./backend.md) § Fetching pipeline.
- **Sharper sources, at ingest** _(2026-09-28)_: a YouTube `hqdefault.jpg` (480 × 360, bars
  and all) is swapped for `hq720.jpg` when a `HEAD` request finds it — cached 30 days, a network
  failure not cached — and a Reddit `preview.redd.it` thumbnail becomes the `i.redd.it`
  original. `external-preview.redd.it` is left alone.
- `alt=""` — the image is decoration beside a title that carries the text.
- Cards `loading="lazy"`; the hero loads eagerly with `fetchpriority="high"`. (Lazy is safe
  on the feed page and the desktop pane; the known trap is images *inside a vaul drawer*, which
  is why the add wizard's avatars stay eager.)
- **A source that declares itself too small answers `null` before anything renders.** When the
  image URL carries its own `width=` and it is under 480 — the smallest size we serve — there is
  no image on the wire and the card is compact from the first paint. Reddit's `media:thumbnail`
  is why: the size is baked into the preview URL and sits inside its `s=` signature, so it can't
  be raised, and 43% of the Reddit images in the dev database declare a width under 480
  _(measured 2026-09-22)_. Only `width`, and only when it parses as a number — a parameter we
  can't read is not evidence, and dropping an image we could have shown is the worse mistake.
  `core/images.py`'s `_declared_too_small`.
- **A failed load removes the box.** The card collapses to its compact shape, the hero
  disappears; no broken-image icon, no grey square left behind. The same happens when an image
  loads narrower than 320px — a tracking pixel, a thumbnail whose URL declared nothing — because
  a blown-up thumb reads worse than none. This is the backstop for sources the rule above can't
  read, and it is a **visible collapse**: the box is laid out, then removed. From stage 2 the
  server knows real dimensions, answers `null` for both cases, and the read-time collapse — and
  the flicker it causes — stops happening. See [backend-roadmap.md](./backend-roadmap.md) § T15d.
- **Two card versions.** Settings → Appearance → *Post cards: Image / Compact*, synced through
  `/settings` like the theme, feed-list and scrollbar settings (a `UserSettings` column). A post
  with no image renders compact under either setting. The default is *Image* — the card
  [screens-and-flows.md](./screens-and-flows.md) § 2 describes has always shown one.
- Feed icons render through Nuxt UI's `UAvatar`, whose initials fallback covers the sources
  that have none, or whose icon fails to load. The wizard passes its own initials (the first
  letter of the first two words that start with a letter or digit), since UAvatar's default
  turns "Vue.js - The progressive…" into "V-".

## Feed icons

_Shipped 2026-09-28 (T15b)._ The rule lives in `core/icons.py`, in this order:

1. **Atom `<icon>`** — square by definition. RSS `<image>` and Atom `<logo>` are **not** used:
   they are logos and banners (RSS caps the image at 144 × 400, Atom asks for 2:1), and a
   64 × 64 crop of one reads worse than initials.
2. **The site's declared icons**, largest first (`rel="icon"`, `apple-touch-icon`; an SVG's
   `sizes="any"` wins; an undeclared size ranks below every declared one, a touch icon at its
   180px default).
3. **`/favicon.ico` at the site's origin**, unverified — a guess that 404s ends as the same
   initials.

A **YouTube channel** is its own case: its face is the avatar in the channel page's `og:image`.
YouTube's declared icons and favicon are the same for every channel, so a YouTube page never
falls back to them; a channel with no avatar found gets initials, not the YouTube logo.

**When it's looked up.** Discovery reads the icon off the page it already fetched, so the
wizard costs no extra request (a feed URL pasted directly, with no page in hand, gets the
favicon guess). At subscribe time ingest looks the icon up once per source when it is blank —
one request before the poll's transaction — and stores the answer under the never-overwrite
rule; a stored icon is never looked up again. Icons only render through `images.icon()`, a
signed `rs:fill-down` 64 × 64 centre crop; imgproxy never enlarges, so a smaller favicon comes
back at its own size, still square.

## Operations

**Stage 1.** `docker-compose.yml` gains an `imgproxy` service on port 8080. Three environment
variables, documented in `.env.example`:

| Variable | Read by | Meaning |
| --- | --- | --- |
| `IMGPROXY_KEY`, `IMGPROXY_SALT` | `api` and `imgproxy` | The shared secret. Django stamps every URL with an HMAC of the path; imgproxy refuses a URL whose stamp doesn't match, so nobody can use the resizer for their own images. Hex strings; the dev fallback is written **once**, in compose, and handed to both services. |
| `IMGPROXY_PUBLIC_URL` | `api` | The base the *browser* reaches imgproxy at — `http://localhost:8080` in dev, `https://img.<domain>` in prod. `dev:mobile` (a phone on the LAN) needs the host's LAN address here, exactly as it does for `NUXT_PUBLIC_API_BASE`. |

An empty key is a supported state, like `YOUTUBE_API_KEY`: every `image` is `null` and the app
renders compact cards. Limits live on the imgproxy service: a 10 MB source cap, a 10 s download
timeout, and imgproxy's default refusal of private, loopback and link-local source addresses —
the SSRF rule `core/fetch.py` had to build by hand, here for free. **Answered by T15a's real-URL
verification, not guessed:** both `preview.redd.it` and `external-preview.redd.it` served
imgproxy's default User-Agent a plain 200, so `IMGPROXY_USER_AGENT` is not needed; the knob
stays undocumented until a real source actually refuses the default.

**Stage 2** adds a `minio` service (bucket created on start) and bucket credentials for `api`,
`worker` and `imgproxy` (`IMGPROXY_USE_S3`, endpoint, keys). Production uses R2 or S3 with the
same variables.

**Stage 3** is DNS and a CDN rule: `img.<domain>` → imgproxy, proxied through Cloudflare;
`IMGPROXY_PUBLIC_URL` set to match.

## Decision log

Decided 2026-09-15, while writing this doc. Append here; don't rewrite past entries.

- **Staged — proxy first, bucket second, paid third.** Judged against "works really nice for
  ≤100 readers, then buy capacity, never box ourselves in". Every shape was compared: hotlink,
  self-hosted proxy, managed transform CDN, a worker pipeline that pre-renders sizes, an origin
  store (originals in a bucket, sizes on demand), managed storage. They differ on two axes only —
  *who makes the sizes* and *whether we keep the original* — and the proxy-then-bucket sequence
  reaches the best end state (the origin store) with each step additive.
- **imgproxy over pre-rendering.** The previous project, crowdfeed, pre-rendered `md` and `lg`
  JPEGs at ingest onto S3 + CloudFront. It runs well and never lost an image — and it has had
  those two sizes, JPEG only, no retina and unresized avatars ever since, because with rendered
  files a new size is a backfill over every post. FeedMe needs more kinds of image than crowdfeed
  did (cards, hero, retina, icons that are ICO or SVG, article images that only exist at read
  time, avatars), so sizes have to be constants. What crowdfeed got right is kept: a media
  hostname with a CDN and long cache in front of a bucket, and fixed 16:9 boxes.
- **Nothing stored in stage 1.** Posts are pruned at 90 days and 63% have no image; a storage
  layer for the ephemeral stream is machinery the first task doesn't need to prove the rest. The
  bucket is the *next* task, not a maybe — permanence is what crowdfeed's readers had.
- **The backend signs; no `@nuxt/image`.** Its imgproxy provider signs on the client, which puts
  the key in the bundle. Plain `<img srcset>` with ready strings from the API is less machinery
  and correct. Nuxt's own `ipx` is out twice over: the Capacitor build has no Nuxt server, and
  ipx can't allowlist arbitrary feed hosts.
- **`srcset` as a string on the wire.** The sizes are the backend's fact; sending widths as data
  would make the frontend re-derive the attribute and let the two lists drift.
- **16:9 fixed boxes, centre crop.** No layout shift and nothing to store, for the price of
  cropping tall images — and the crop is what cleans YouTube's posters. Natural-aspect rendering
  needs dimensions, which stage 2 brings; it can be revisited then.
- **Two card versions as a synced setting.** [product-overview.md](./product-overview.md)
  § Planned already named the image / compact card style; it follows the pattern of the three
  appearance settings that exist, column and all.
- **Article images are rewritten at read time**, in the endpoint, never into the cached
  `article_html` column: a signature baked into the cache would break every cached article on
  a key rotation.
- **Not chosen now:** a managed transform CDN (needs a deploy target and a hostname
  [backend.md](./backend.md) explicitly defers; dev would hit a paid service from localhost);
  managed storage such as Cloudflare Images (paid from day one and scales with stored images
  rather than views; the originals live with the vendor); resizing inside Django with Pillow
  (image work occupying web workers, and SSRF, caching and formats rebuilt by hand).

Decided 2026-09-22, verified while building T15a:

- **`fill-down`, not `fill`.** The recipe drafted here was `rs:fill:{w}:{h}`. Measured against a
  real YouTube `hqdefault.jpg` — not a fixture — imgproxy's `fill` skips the crop entirely when
  the source is smaller than the requested size and enlarging is off, so the poster came back
  480 × 360, letterbox and all: exactly what the centre-crop bullet above exists to remove.
  `fill-down` shrinks the *requested* size to fit the source instead, so the crop still runs at
  whatever size the source allows (480 × 270 for that poster, 640 × 360 for a Reddit preview,
  960 × 540 for a full-size blog hero). § Sizes and formats amended in place.
- **`IMGPROXY_USER_AGENT` is not needed.** Settles the question § Operations left open for this
  task's real-URL pass: both `preview.redd.it` and `external-preview.redd.it` served imgproxy's
  default User-Agent a plain 200, so nothing Reddit-specific was required. The knob stays
  undocumented until a real source actually refuses the default.
- **The 320px floor fired on a real image, not only a contrived one.** A Medium CDN image
  proxied at 188 × 106 — under the floor — confirmed `PostImage.vue`'s collapse-on-too-small
  rule (§ Rendering) against a source that actually exists, alongside the dead-URL (404, card
  collapses) and tampered-signature (403) cases the plan already called for.
- **A declared width under 480 answers `null` server-side** _(added 2026-09-23)_. The read-time
  collapse turned out to be the *common* case, not the edge one: 10 of the 25 newest posts came
  back under 320px, so four cards in ten laid out a grey box and then took it away. Root cause
  was upstream of the image code — Reddit's RSS hands out preview URLs with the size in them,
  and 207 of 477 stored Reddit images declare a width of 140, 216 or 320. The feed declares no
  dimensions of its own (Reddit's `media:thumbnail` carries a url and nothing else, measured),
  so the URL's own `width=` is the only thing knowable before the bytes arrive — and acting on
  it costs no network call, no column and no backfill. After the rule, every image still served
  in that sample came back 480 × 270 and nothing flickered. Rejected on the way: pre-loading the
  image hidden and revealing the box only once it proved big enough (kills the flicker, but
  `loading="lazy"` and `display:none` don't combine, so cards would lose lazy loading, and the
  list would reflow as images arrived instead); and letting small images upscale into the box
  (blurry, which is the thing the floor exists to prevent).

Decided 2026-09-23, verified while building T15c:

- **Fit, not fill — and no width floor.** Unlike the card family, an article's pictures are the
  author's own framing: `rs:fit:1920:0` shrinks to the reading width without cropping, and
  nothing stops a small inline image from staying small, since imgproxy's `fit` never enlarges
  it anyway. `_card`'s fill-down 16:9 recipe stays a card-and-hero thing only.
- **An unproxiable `<img>` is dropped with its tag** — a relative or scheme-relative `src`, or
  every image when there's no key — rather than left in the markup with no `src`, which the
  browser would still draw as a broken-image icon. The rewrite runs as a second `nh3.clean` pass
  over the same allowlist, using its `attribute_filter` for the swap; the one regex the code
  carries (dropping a tag the filter answered `None` for) is sound only over nh3's own
  canonical serialisation, which is why it's a second pass rather than one.
- **Verified against real URLs, not only the suite.** simonwillison.net's article extracted
  live with all 14 images rewritten; 25 proxied URLs across the dev database's 9 cached articles
  came back 200 `image/webp`, with one exception — board.flatassembler.net, whose own server
  fails imgproxy's TLS handshake (the source's problem, not the proxy's; renders as the
  browser's broken image, per § Rendering). kk.org's suggested test URL 404'd on the day, so
  simonwillison.net stood in as the live case.
- **Not fixed here, noted for later:** imgproxy's default `IMGPROXY_MAX_ANIMATION_FRAMES=1`
  means an animated GIF inside an article arrives as its still first frame.

Decided 2026-09-28, while building T15b:

- **Atom `<icon>` only; RSS `<image>` and Atom `<logo>` dropped.** The earlier ingest took the
  first of `icon` / `logo` / `image`, but the latter two are banners and logos, not squares —
  centre-cropped to 64 × 64 they read worse than initials. The site's own declared icons come
  next instead.
- **YouTube uses the channel's `og:image`, never YouTube's own icons.** Its declared icons and
  favicon are identical for every channel, which would make every YouTube feed look the same.
- **The `/favicon.ico` guess is unverified.** It costs nothing, and a 404 ends as the same
  initials the feed would have shown anyway.
