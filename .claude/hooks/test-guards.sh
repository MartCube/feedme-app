#!/usr/bin/env bash
# Fixture tests for the PreToolUse guards. Run: bash .claude/hooks/test-guards.sh
# Each line: expected exit code, label, guard, stdin JSON. Exit 2 = blocked, 0 = allowed.
# Keep the fixtures in this file — pasting them into a shell command trips guard-bash itself.
cd "$(dirname "$0")/../.." || exit 1
export CLAUDE_PROJECT_DIR=$PWD
G=.claude/hooks/guard-conventions.sh; B=.claude/hooks/guard-bash.sh; fail=0
t() { local want=$1 label=$2 script=$3 json=$4 out rc
  out=$(printf '%s' "$json" | bash "$script" 2>&1); rc=$?
  if [ "$rc" = "$want" ]; then echo "ok   [$rc] $label"; else echo "FAIL [$rc want $want] $label — $out"; fail=1; fi; }
p() { printf '{"tool_name":"%s","tool_input":{"file_path":"%s/%s"}}' "$1" "$PWD" "$2"; }
c() { printf '{"tool_input":{"command":"%s","run_in_background":%s}}' "$1" "${2:-false}"; }

echo "--- guard-conventions"
t 2 "api.d.ts edit"                 $G "$(p Edit app/types/api.d.ts)"
t 2 "migration write"               $G "$(p Write backend/core/migrations/0009_foo.py)"
t 0 "migrations/__init__"           $G "$(p Edit backend/core/migrations/__init__.py)"
t 2 "new root NOTES.md"             $G "$(p Write NOTES.md)"
t 2 "new app/foo.md"                $G "$(p Write app/foo.md)"
t 0 "new docs/x.md"                 $G "$(p Write docs/x.md)"
t 0 "new .claude/memory/x.md"       $G "$(p Write .claude/memory/x.md)"
t 0 "root README.md write"          $G "$(p Write README.md)"
t 0 "outside project"               $G '{"tool_name":"Write","tool_input":{"file_path":"/home/martcube/.claude/plans/x.md"}}'
t 0 "Edit of md elsewhere"          $G "$(p Edit backend/README.md)"
t 2 ".env"                          $G "$(p Edit .env)"
t 0 ".env.example"                  $G "$(p Edit .env.example)"
t 2 "lockfile"                      $G "$(p Edit pnpm-lock.yaml)"
t 2 "pages/settings"                $G "$(p Write app/pages/settings.vue)"
t 0 "ordinary vue"                  $G "$(p Edit app/components/Navbar.vue)"

echo "--- guard-bash"
t 2 "pnpm dev fg"                   $B "$(c 'pnpm dev')"
t 0 "pnpm dev bg"                   $B "$(c 'pnpm dev' true)"
t 2 "pnpm dev:mobile fg"            $B "$(c 'pnpm dev:mobile')"
t 2 "chained pnpm run dev"          $B "$(c 'cd app && pnpm run dev')"
t 0 "dev inside a pipe filter"      $B "$(c 'pnpm ls | grep dev')"
t 2 "compose up fg"                 $B "$(c 'docker compose up api')"
t 0 "compose up -d"                 $B "$(c 'docker compose up -d db redis')"
t 0 "compose up --detach"           $B "$(c 'docker compose up --detach')"
t 0 "compose up bg"                 $B "$(c 'docker compose up api' true)"
t 0 "compose ps"                    $B "$(c 'docker compose ps')"
t 2 "runserver"                     $B "$(c 'docker compose exec api python manage.py runserver')"
t 2 "npx"                           $B "$(c 'npx vue-tsc --noEmit')"
t 2 "npm install"                   $B "$(c 'npm install foo')"
t 2 "yarn after chain"              $B "$(c 'cd x; yarn add y')"
t 0 "pnpm dlx"                      $B "$(c 'pnpm dlx chrome-devtools-mcp@latest')"
t 0 "npm as a word in text"         $B "$(c 'grep -r npm docs/')"
t 0 "empty"                         $B '{"tool_input":{}}'
# heredoc bodies are data, not commands
t 0 "pnpm dev inside heredoc"       $B "$(c 'cat > x.md <<'"'"'EOF'"'"'\npnpm dev   # :3000\nEOF')"
t 0 "npm inside unquoted heredoc"   $B "$(c 'cat <<EOF\nnpm install\nEOF')"
t 2 "pnpm dev after heredoc ends"   $B "$(c 'cat <<EOF\nhello\nEOF\npnpm dev')"
t 0 "here-string is not a heredoc"  $B "$(c 'grep dev <<<pnpm')"
exit $fail
