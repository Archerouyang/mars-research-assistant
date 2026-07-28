#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_URL="${MARS_REPOSITORY_URL:-https://github.com/archerthegoat/mars-research-assistant.git}"
REPOSITORY_REF="${MARS_REPOSITORY_REF:-master}"
TARGET="${MARS_SKILL_TARGET:-${HOME}/.codex/skills/mars-research-assistant}"

for command_name in curl git; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "$command_name is required for the one-command installer" >&2
    exit 69
  fi
done

UV_EXECUTABLE="$(command -v uv 2>/dev/null || true)"
if [[ -z "$UV_EXECUTABLE" ]]; then
  echo "uv was not found; installing uv with the official installer"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  for candidate in "${HOME}/.local/bin/uv" "${HOME}/.cargo/bin/uv"; do
    if [[ -x "$candidate" ]]; then
      UV_EXECUTABLE="$candidate"
      break
    fi
  done
fi
if [[ -z "$UV_EXECUTABLE" || ! -x "$UV_EXECUTABLE" ]]; then
  echo "uv installation did not provide an executable" >&2
  exit 69
fi

INSTALL_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/mars-skill-install.XXXXXX")"
cleanup() {
  rm -rf "$INSTALL_ROOT"
}
trap cleanup EXIT

git clone --quiet --depth 1 --branch "$REPOSITORY_REF" \
  "$REPOSITORY_URL" "$INSTALL_ROOT/source"

env PATH="$(dirname "$UV_EXECUTABLE"):$PATH" \
  bash "$INSTALL_ROOT/source/scripts/install-mars-skill.sh" \
  --target "$TARGET"

echo "Mars Research Assistant is ready at $TARGET"
