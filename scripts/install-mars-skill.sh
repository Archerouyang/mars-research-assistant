#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_ID=""
TARGET=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill)
      SKILL_ID="${2:-}"
      shift 2
      ;;
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    *)
      echo "usage: $0 --skill <skill-id> --target <skills-directory>" >&2
      exit 64
      ;;
  esac
done

if [[ -z "$SKILL_ID" || -z "$TARGET" ]]; then
  echo "usage: $0 --skill <skill-id> --target <skills-directory>" >&2
  exit 64
fi
if [[ ! "$SKILL_ID" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "invalid Mars Skill id: $SKILL_ID" >&2
  exit 65
fi
if ! grep -Fq "\"id\": \"$SKILL_ID\"" "$ROOT/mars-skills.json"; then
  echo "unknown Mars Skill: $SKILL_ID" >&2
  exit 65
fi

SOURCE="$ROOT/skills/$SKILL_ID"
if [[ ! -f "$SOURCE/SKILL.md" ]]; then
  echo "unknown Mars Skill: $SKILL_ID" >&2
  exit 65
fi
if find "$SOURCE" -type l -print -quit | grep -q .; then
  echo "Skill contains a symbolic link: $SKILL_ID" >&2
  exit 65
fi

mkdir -p "$TARGET"
TARGET_ROOT="$(cd "$TARGET" && pwd -P)"
DESTINATION="$TARGET_ROOT/$SKILL_ID"
if [[ "$DESTINATION" != "$TARGET_ROOT/"* ]]; then
  echo "invalid installation destination" >&2
  exit 65
fi
if [[ -e "$DESTINATION" || -L "$DESTINATION" ]]; then
  echo "destination already exists: $DESTINATION" >&2
  exit 73
fi

cp -R "$SOURCE" "$DESTINATION"
echo "installed $SKILL_ID to $DESTINATION"
