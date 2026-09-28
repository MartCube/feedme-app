---
name: reference-crowdfeed
description: "crowdfeed.com — the user's previous news-aggregator project (still live); their baseline for infra decisions, especially images; code is on another laptop"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 6c51f4e2-caf5-4166-9dfc-39ef82cc03c2
  modified: 2026-09-28T20:55:05.544Z
---

**crowdfeed** (https://crowdfeed.com, Nuxt on nginx) is the user's earlier aggregator and,
alongside Reeder, a named **product/UI inspiration** for FeedMe (recorded in
docs/product-overview.md) — look at it when designing post cards and layouts, not only infra.
It is also the mental model they compare FeedMe's infrastructure against. Observed from outside on
2026-09-15: images pre-rendered at ingest into two 16:9 JPEGs (`md` 576×324, `lg` 1000×563)
on S3 behind CloudFront at `media.crowdfeed.com`, 120-day cache, no srcset/WebP, avatars
stored unresized. FeedMe's images strategy (docs/images.md) keeps its media-domain + CDN +
fixed-16:9 ideas and rejects the pre-rendering.

**How to apply:** when an infra question comes up (storage, CDN, jobs), ask what crowdfeed did
— it's a working production reference the user trusts. The project's source is on their other
laptop; they offered to share it if the code (not just the live behaviour) matters.
Related: [[feedback-strategy-decisions]].
