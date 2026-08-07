#!/usr/bin/env bash
# PreToolUse guard for Write|Edit. Blocks edits that violate FeedMe invariants.
# Exit 2 = block; stderr is fed back to Claude as the reason.
set -uo pipefail

path=$(jq -r '.tool_input.file_path // empty')
[ -z "$path" ] && exit 0

# Normalise to a repo-relative path when possible.
rel=${path#"${CLAUDE_PROJECT_DIR:-}/"}
base=$(basename "$path")

# 1. Local env files are gitignored secrets. .env.example is the tracked template.
if [[ "$base" == .env || "$base" == .env.* ]] && [[ "$base" != .env.example ]]; then
  echo "Blocked: $base is a gitignored local env file. Edit .env.example instead and tell the user which values to set locally." >&2
  exit 2
fi

# 2. Lockfile is pnpm's to write.
if [[ "$base" == pnpm-lock.yaml ]]; then
  echo "Blocked: pnpm-lock.yaml is generated. Change package.json and run 'pnpm install'." >&2
  exit 2
fi

# 3. Drawers mount in the layout, never as nested route pages — a nested route
#    remounts the host page (see .claude/memory/project-gotchas.md).
if [[ "$rel" =~ ^app/pages/(settings|add|edit) ]]; then
  echo "Blocked: $rel would make a drawer a nested route page. Nested routes remount the host page. Drawers mount in the layout (app/layouts/) and open from the URL — see CLAUDE.md and .claude/memory/project-gotchas.md." >&2
  exit 2
fi

exit 0
