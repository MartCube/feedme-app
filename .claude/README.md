# Claude Code setup for FeedMe

Human-facing map of what lives in `.claude/` and how a working day runs. Nothing in this file is
loaded into Claude's context — `CLAUDE.md` is the machine-facing summary, this is the why.

## A working day

1. Start a session. The SessionStart hook prints the roadmap's next task, whether the `api`
   container is up, and the git state — no need to ask.
2. Build. Reading a file under `app/` or `backend/` pulls the matching rule file into context;
   skills (`frontend-dev`, `backend-dev`) are the how-to when you need it.
3. `/commit <intent>` runs the chain: `checker` (+ `design-reviewer` when UI changed) → `docs`
   → `git`. A red checker means no commit.
4. The status line shows `ctx:%` (context used) and `5h:%` / `7d:%` (the Pro-plan windows).
   Pace the day by those, and `/compact` at a phase boundary rather than mid-task.

## What's here, and when it costs context

| Path | What | Enters context |
|---|---|---|
| `CLAUDE.md` | Project instructions — spec-first, the commit chain, pointers | every session |
| `rules/` | Hard rules, path-scoped: `components`, `shell`, `data-layer`, `backend` | on reading a matching file |
| `skills/` | `frontend-dev`, `backend-dev`, `verify`; `new-component` and `commit` are user-invoked only | on invocation |
| `agents/` | Railed subagents — table below | on spawn |
| `hooks/` | `guard-conventions.sh` (Write/Edit), `guard-bash.sh` (Bash), `session-status.sh` (SessionStart); `test-guards.sh` runs the fixtures | never — deterministic shell |
| `memory/` | Auto-memory. `MEMORY.md` is the index; topic files are read on demand | index every session |
| `settings.json` | Hook wiring (committed); `settings.local.json` holds permissions (gitignored) | — |
| `superpowers/` | Plans, specs and scratch written by the superpowers plugin | — |

## Agents

| Agent | Model | Job | Writes? |
|---|---|---|---|
| `checker` | haiku | lint + typecheck; ruff + pytest + migrations check when `backend/` changed | no |
| `git` | haiku | stage, commit, push on request; proposes-and-stops when ambiguous | git only |
| `design-reviewer` | sonnet | drift from `docs/design-system.md` on changed `.vue`/`.css` | no |
| `docs` | sonnet | sync `docs/` with what was built; audits on demand | `docs/` only |
| `librarian` | sonnet | current library docs via context7 before writing against an unfamiliar API | no |
| `explorer` | sonnet | read-only code search, only when asked for by name | no |

Tiers follow failure cost: mechanical and railed → haiku, judgment or prose → sonnet, the main
loop stays on Opus. Agent files are read at session start — restart after editing one.

## Budget rules (Pro plan)

- A rule that must always hold becomes a **hook** (zero tokens), not a sentence in CLAUDE.md.
  Every guard has a fixture in `hooks/test-guards.sh` — run it after touching a guard.
- Context loads only when relevant: rules by path, skills on invocation, memory by index.
- No opus subagents. No `type: prompt` / `type: agent` hooks. No config-collection plugins —
  `everything-claude-code` was reviewed on 2026-09-16; the guards, session hook, rule scoping,
  model tiers and status line are what survived, the rest was duplicative or token-costly.

## Changing things

- New hard rule for one part of the tree → the matching `rules/*.md`. New always-on fact →
  `CLAUDE.md`, and keep it short. New how-to → the skill.
- New invariant → a guard branch plus a fixture. Hooks reload live; rules load live.
- Vocabulary (`Feed`, `Folder`, `Post`, `Saved`; `Source` backend-only) is decided in
  `docs/backend.md` § Vocabulary — not here, not in a rule.
