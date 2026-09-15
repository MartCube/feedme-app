---
name: feedback-network-features-real-urls
description: Fetch/parse features and background jobs aren't done on a green suite — prove them against real messy URLs and the real dev database first
metadata:
  type: feedback
---

A passing pytest suite is not evidence that a feature touching the outside world, or the
database over time, actually works. The fixtures are data we wrote, so they only prove the code
does what we already assumed. Two shapes this takes:

**Fetching or parsing third-party pages/feeds** (discovery, ingest, extraction) — run it against
a spread of **real live URLs** and paste the results, picking the *messy* shapes:

- the URL actually in a user's address bar (a deep article/post URL), not just the section index
- each source type the feature claims to cover, on its real site, not a fixture of it
- at least one page from a big JS app (YouTube et al.), where the markup breaks normal assumptions

**Background jobs and anything that changes data over time** (polling, retention, schedulers) —
run it against the **real dev database with the other jobs still running**. Unit tests exercise
one job in isolation, so two jobs that undo each other stay invisible no matter how green the
suite is. Check the effect *persists* after the next cycle of everything else, rather than
checking only that the job did its own work.

**Why:** the user tests by hand and finds these in minutes. On T11a the suite was 231-green while
a pasted post URL and a pasted YouTube channel URL both resolved to nothing. On T13 it was
285-green while the nightly prune and the five-minute poll sweep deleted and recreated the same
rows forever — neither shape was in the fixtures, so nothing failed.

**How to apply:** put the live run in the plan's verification section as its own step, and do it
*before* reporting completion, not after. Measure and report the cause when one fails (byte
offsets, what the page actually declared, which job wrote the row back) rather than guessing. See
[[feedback-verification-approach]].
