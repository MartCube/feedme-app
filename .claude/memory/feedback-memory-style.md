---
name: feedback-memory-style
description: Memories store rules and how to avoid problems — never the details of specific incidents
metadata:
  type: feedback
---

When writing or updating memories: keep the rule, the short why, and how to apply it. Do not
record the details of specific incidents (dates, quotes, blow-by-blow stories) — if we know how
to avoid an incident, the story adds nothing. One file per rule; each file's name says exactly
what's inside.

**How to apply:** before saving a memory, strip it to rule + why + how-to-apply. Prefer updating
an existing file over creating a near-duplicate. Point to `docs/` for anything the repo already
records instead of copying it.

**Ownership split with CLAUDE.md** (agreed): `CLAUDE.md` (git-tracked, seen by any tool) owns
repo facts — stack, conventions, folder contracts, definition of done. Memory (gitignored,
personal) owns the working relationship and learned traps. Never state the same fact in both;
neither stores anything derivable from repo files with one cheap read (e.g. package.json scripts).
