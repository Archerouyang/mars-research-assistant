#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET=""

usage() {
  echo "usage: $0 --target <skills-directory>" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    *)
      usage
      exit 64
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  usage
  exit 64
fi

SKILL_IDS=()
while IFS= read -r identifier; do
  SKILL_IDS+=("$identifier")
done < <(sed -n 's/^[[:space:]]*"id": "\([a-z0-9-]*\)",[[:space:]]*$/\1/p' "$ROOT/mars-skills.json")

if [[ "${#SKILL_IDS[@]}" -eq 0 ]]; then
  echo "no Mars Skills found in collection manifest" >&2
  exit 65
fi

for identifier in "${SKILL_IDS[@]}"; do
  if [[ ! "$identifier" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
    echo "invalid Mars Skill id: $identifier" >&2
    exit 65
  fi
  if ! grep -Fq "\"id\": \"$identifier\"" "$ROOT/mars-skills.json"; then
    echo "unknown Mars Skill: $identifier" >&2
    exit 65
  fi
  source="$ROOT/skills/$identifier"
  if [[ ! -f "$source/SKILL.md" ]]; then
    echo "unknown Mars Skill: $identifier" >&2
    exit 65
  fi
  if find "$source" -type l -print -quit | grep -q .; then
    echo "Skill contains a symbolic link: $identifier" >&2
    exit 65
  fi
done

mkdir -p "$TARGET"
TARGET_ROOT="$(cd "$TARGET" && pwd -P)"
for identifier in "${SKILL_IDS[@]}"; do
  destination="$TARGET_ROOT/$identifier"
  if [[ "$destination" != "$TARGET_ROOT/"* ]]; then
    echo "invalid installation destination" >&2
    exit 65
  fi
  if [[ -e "$destination" || -L "$destination" ]]; then
    echo "destination already exists: $destination" >&2
    exit 73
  fi
done

STAGING_ROOT="$(mktemp -d "$TARGET_ROOT/.mars-skills-stage.XXXXXX")"
cleanup() {
  if [[ -d "$STAGING_ROOT" ]]; then
    rm -rf "$STAGING_ROOT"
  fi
}
trap cleanup EXIT

for identifier in "${SKILL_IDS[@]}"; do
  cp -R "$ROOT/skills/$identifier" "$STAGING_ROOT/$identifier"
done
for identifier in "${SKILL_IDS[@]}"; do
  mv "$STAGING_ROOT/$identifier" "$TARGET_ROOT/$identifier"
done
rmdir "$STAGING_ROOT"
trap - EXIT

echo "installed all ${#SKILL_IDS[@]} Mars Skills to $TARGET_ROOT"
