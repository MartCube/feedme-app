#!/usr/bin/env bash
# PreToolUse guard for Bash. Blocks commands that waste a turn or fight the toolchain.
# Exit 2 = block; stderr is fed back to Claude as the reason.
set -uo pipefail

input=$(cat)
cmd=$(jq -r '.tool_input.command // empty' <<<"$input")
bg=$(jq -r '.tool_input.run_in_background // false' <<<"$input")
[ -z "$cmd" ] && exit 0

# Heredoc bodies are data (a skill file that documents `pnpm dev`), not commands — drop them
# before matching. The `<<TAG` line itself is kept; lines after the closing tag resume.
code=$(awk -v q="'" '
  BEGIN { re = "(^|[^<])<<-?[\"" q "]?[A-Za-z_][A-Za-z0-9_]*" }
  skip { if ($0 ~ ("^[[:space:]]*" tag "$")) skip = 0; next }
  match($0, re) { tag = substr($0, RSTART, RLENGTH); sub("^.?<<-?[\"" q "]?", "", tag); skip = 1 }
  { print }' <<<"$cmd")

# 1. Long-running servers hang the tool call until its timeout unless backgrounded.
#    Match at a command start (line start or after ; && || |), so 'pnpm ls | grep dev' passes.
if [[ "$bg" != true ]]; then
  if grep -qE '(^|[;&|]) *(pnpm (run )?dev(:mobile)?|nuxt dev|(pnpm exec )?nuxi? dev)\b' <<<"$code"; then
    echo "Blocked: 'pnpm dev' in the foreground hangs this tool call until timeout. Run it with run_in_background: true, then poll 'curl -sf localhost:3000'." >&2
    exit 2
  fi
  if grep -qE '(^|[;&|]) *docker compose up\b' <<<"$code" && ! grep -qE 'docker compose up[^;&|]*( -d| --detach)' <<<"$code"; then
    echo "Blocked: 'docker compose up' in the foreground hangs this tool call. Use 'docker compose up -d …'; for the stream, background 'docker compose logs -f api'." >&2
    exit 2
  fi
  if grep -qE 'manage\.py runserver' <<<"$code"; then
    echo "Blocked: runserver in the foreground hangs this tool call. Django runs inside the api container — 'docker compose up -d api'." >&2
    exit 2
  fi
fi

# 2. Node here is pnpm-managed: npm/npx/yarn are not reliably on PATH and would write a
#    foreign lockfile (see .claude/memory/project-gotchas.md).
if grep -qE '(^|[;&|]) *(npm|npx|yarn)\b' <<<"$code"; then
  echo "Blocked: this repo is pnpm-only. Use 'pnpm add' / 'pnpm exec <bin>' / 'pnpm dlx <pkg>' instead of npm/npx/yarn." >&2
  exit 2
fi

exit 0
