#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="${1:-$ROOT}"
SMOKE_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/mars-research-assistant-skill-smoke.XXXXXX")"
trap 'rm -rf "$SMOKE_ROOT"' EXIT

export HOME="$SMOKE_ROOT/home"
export CODEX_HOME="$SMOKE_ROOT/codex"
export CLAUDE_CONFIG_DIR="$SMOKE_ROOT/claude"
export XDG_CONFIG_HOME="$SMOKE_ROOT/xdg"
export npm_config_cache="$SMOKE_ROOT/npm-cache"
export NO_UPDATE_NOTIFIER=1

mkdir -p \
  "$HOME" \
  "$CODEX_HOME" \
  "$CLAUDE_CONFIG_DIR" \
  "$XDG_CONFIG_HOME" \
  "$npm_config_cache"

npx --yes skills@latest add "$SOURCE" --list > "$SMOKE_ROOT/discovery.txt"
grep -F "Found 1 skill" "$SMOKE_ROOT/discovery.txt" >/dev/null
grep -F "mars-research-assistant" "$SMOKE_ROOT/discovery.txt" >/dev/null

npx --yes skills@latest add "$SOURCE" \
  --skill mars-research-assistant \
  --agent codex claude-code \
  --global \
  --yes \
  --copy \
  > "$SMOKE_ROOT/install.txt"

CANONICAL="$ROOT/skills/mars-research-assistant"
CODEX_INSTALL="$HOME/.agents/skills/mars-research-assistant"
CLAUDE_INSTALL="$CLAUDE_CONFIG_DIR/skills/mars-research-assistant"

for installed in "$CODEX_INSTALL" "$CLAUDE_INSTALL"; do
  test -f "$installed/SKILL.md"
  test -f "$installed/references/macro-research.md"
  test -f "$installed/references/instrument-research.md"
  test -f "$installed/scripts/stateless_research_run.py"
  test -f "$installed/scripts/verify_stateless_research_run_selftest.py"
  diff -qr "$CANONICAL" "$installed" >/dev/null
  if find "$installed" -type f \( \
    -name '.env' -o \
    -name 'auth.json' -o \
    -name 'credentials.json' \
  \) | grep -q .; then
    echo "private configuration leaked into installed Skill: $installed" >&2
    exit 1
  fi
done

if grep -R -E '/Users/[^/]+/(Documents|Library)/' \
  "$CODEX_INSTALL" "$CLAUDE_INSTALL" >/dev/null; then
  echo "private absolute path leaked into installed Skill" >&2
  exit 1
fi

echo "portable Skill isolated install smoke ok"
echo "source=$SOURCE"
echo "real agent homes untouched; temporary root removed on exit"
