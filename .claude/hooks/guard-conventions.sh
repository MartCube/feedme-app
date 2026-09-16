#!/usr/bin/env bash
# PreToolUse guard for Write|Edit. Blocks edits that violate FeedMe invariants.
# Exit 2 = block; stderr is fed back to Claude as the reason.
set -uo pipefail

input=$(cat)
path=$(jq -r '.tool_input.file_path // empty' <<<"$input")
tool=$(jq -r '.tool_name // empty' <<<"$input")
[ -z "$path" ] && exit 0

# Normalise to a repo-relative path when possible.
root=${CLAUDE_PROJECT_DIR:-}
rel=${path#"$root/"}
base=$(basename "$path")
inside=0
[ -n "$root" ] && [[ "$path" == "$root"/* ]] && inside=1

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

# 4. Generated files are regenerated, never hand-edited.
if [[ "$rel" == app/types/api.d.ts ]]; then
  echo "Blocked: app/types/api.d.ts is generated from the live OpenAPI schema. Change the backend Schema, then run 'pnpm types:api' with the API up." >&2
  exit 2
fi
if [[ "$rel" =~ ^backend/.*/migrations/[0-9]+_[^/]+\.py$ ]]; then
  echo "Blocked: migrations are generated. Change the model, then 'docker compose exec api python manage.py makemigrations' and commit the result." >&2
  exit 2
fi

# 5. New markdown has three homes: docs/ (product spec), .claude/ (plans, memory, skills),
#    pending_tasks/ (the user's backlog). Root README.md and CLAUDE.md are the only exceptions.
#    Only creation is guarded — editing an existing file elsewhere is fine. Files outside the
#    project (e.g. ~/.claude/plans/) are not ours to police.
if [[ "$tool" == Write && $inside -eq 1 && "$rel" == *.md ]] \
  && [[ ! "$rel" =~ ^(docs|\.claude|pending_tasks)/ ]] \
  && [[ "$rel" != README.md && "$rel" != CLAUDE.md ]] \
  && [ ! -e "$path" ]; then
  echo "Blocked: new markdown belongs in docs/ (product spec), .claude/ (plans, specs, scratch, memory) or pending_tasks/ — not $rel. See .claude/memory/project-claude-dir-layout.md." >&2
  exit 2
fi

exit 0
