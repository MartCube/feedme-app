#!/usr/bin/env bash
# SessionStart hook. Stdout becomes context for the first turn — keep it short.
# Answers the three things every FeedMe session otherwise spends tool calls on:
# what's next on the roadmap, whether the API is up, and the state of the tree.
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

echo "FeedMe status"

next=$(awk '/^\*\*Next up:\*\*/{f=1} f{print; n++} n>=3{exit}' docs/backend-roadmap.md 2>/dev/null \
  | tr '\n' ' ' | sed -E 's/\*\*//g; s/_\(([^)]*)\)_/(\1)/g; s/ +/ /g' | cut -c1-220)
[ -n "$next" ] && echo "- Roadmap: ${next}…"

if timeout 3 docker compose ps --status running --services 2>/dev/null | grep -qx api; then
  echo "- Backend: api container up"
else
  echo "- Backend: api container DOWN — nothing renders until 'docker compose up -d'"
fi

dirty=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
head=$(git log -1 --format='%h %s' 2>/dev/null)
echo "- Git: $dirty uncommitted · HEAD $head"
exit 0
