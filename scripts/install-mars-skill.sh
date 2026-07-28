#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET=""
FORCE=false

usage() {
  echo "usage: $0 --target <managed-package-directory> [--force]" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --force)
      FORCE=true
      shift
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
if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required; no pip fallback is supported" >&2
  exit 69
fi
for required in SKILL.md LICENSE pyproject.toml uv.lock mars-skills.json package-files.txt; do
  if [[ ! -f "$SOURCE_ROOT/$required" ]]; then
    echo "source package is missing $required" >&2
    exit 65
  fi
done
if find "$SOURCE_ROOT/scripts" "$SOURCE_ROOT/skills" -type l -print -quit | grep -q .; then
  echo "source package contains a symbolic link" >&2
  exit 65
fi
TRUSTED_PYTHON=""
if [[ -n "${UV_PYTHON:-}" && -x "${UV_PYTHON}" ]]; then
  TRUSTED_PYTHON="$UV_PYTHON"
elif ! TRUSTED_PYTHON="$(uv python find --no-project '>=3.12,<3.13' 2>/dev/null)"; then
  uv python install 3.12
  TRUSTED_PYTHON="$(
    uv python find --managed-python --no-project '>=3.12,<3.13'
  )"
fi
if [[ -z "$TRUSTED_PYTHON" || ! -x "$TRUSTED_PYTHON" ]]; then
  echo "uv could not provide a trusted Python 3.12 interpreter" >&2
  exit 69
fi

TARGET_PARENT_INPUT="$(dirname "$TARGET")"
TARGET_NAME="$(basename "$TARGET")"
if [[ -z "$TARGET_NAME" || "$TARGET_NAME" == "." || "$TARGET_NAME" == ".." ]]; then
  echo "invalid managed package destination" >&2
  exit 65
fi
mkdir -p "$TARGET_PARENT_INPUT"
TARGET_PARENT="$(cd "$TARGET_PARENT_INPUT" && pwd -P)"
TARGET_ROOT="$TARGET_PARENT/$TARGET_NAME"
STAGING_ROOT="$(mktemp -d "$TARGET_PARENT/.mars-package-stage.XXXXXX")"
BACKUP_ROOT=""

cleanup() {
  if [[ -n "$BACKUP_ROOT" && -d "$BACKUP_ROOT" && ! -e "$TARGET_ROOT" ]]; then
    mv "$BACKUP_ROOT" "$TARGET_ROOT"
    BACKUP_ROOT=""
  fi
  if [[ -d "$STAGING_ROOT" ]]; then
    rm -rf "$STAGING_ROOT"
  fi
}
trap cleanup EXIT

REUSE_ENVIRONMENT=false
MANAGED_INSTALL_VALID=false
if [[ -e "$TARGET_ROOT" || -L "$TARGET_ROOT" ]]; then
  if [[ ! -d "$TARGET_ROOT" || ! -f "$TARGET_ROOT/.mars-managed.json" ]]; then
    echo "destination already exists and is not managed: $TARGET_ROOT" >&2
    exit 73
  fi
  if "$TRUSTED_PYTHON" \
    "$SOURCE_ROOT/scripts/managed_package.py" verify --root "$TARGET_ROOT"; then
    MANAGED_INSTALL_VALID=true
  else
    if [[ "$FORCE" != true ]]; then
      echo "managed destination was customized; rerun with --force to replace it" >&2
      exit 74
    fi
  fi
fi

while IFS= read -r relative || [[ -n "$relative" ]]; do
  if [[ -z "$relative" || "$relative" == /* || "$relative" == *".."* ]]; then
    echo "invalid package allowlist entry: $relative" >&2
    exit 65
  fi
  source_path="$SOURCE_ROOT/$relative"
  destination_path="$STAGING_ROOT/$relative"
  if [[ -L "$source_path" || ! -f "$source_path" ]]; then
    echo "package allowlist entry is missing or symbolic: $relative" >&2
    exit 65
  fi
  mkdir -p "$(dirname "$destination_path")"
  cp -p "$source_path" "$destination_path"
done < "$SOURCE_ROOT/package-files.txt"

if [[ "$MANAGED_INSTALL_VALID" == true ]]; then
  OLD_LOCK_HASH="$("$TRUSTED_PYTHON" \
    "$SOURCE_ROOT/scripts/managed_package.py" lock-hash --root "$TARGET_ROOT")"
  if command -v shasum >/dev/null 2>&1; then
    NEW_LOCK_HASH="$(shasum -a 256 "$STAGING_ROOT/uv.lock" | awk '{print $1}')"
  elif command -v sha256sum >/dev/null 2>&1; then
    NEW_LOCK_HASH="$(sha256sum "$STAGING_ROOT/uv.lock" | awk '{print $1}')"
  else
    echo "a SHA-256 checksum tool is required" >&2
    exit 69
  fi
  if [[ "$OLD_LOCK_HASH" == "$NEW_LOCK_HASH" ]]; then
    cp -R "$TARGET_ROOT/.venv" "$STAGING_ROOT/.venv"
    REUSE_ENVIRONMENT=true
  fi
fi

if [[ "$REUSE_ENVIRONMENT" == true ]]; then
  bash \
    "$STAGING_ROOT/skills/technical-analysis/scripts/ensure_yfinance_environment.sh" \
    --offline
else
  bash \
    "$STAGING_ROOT/skills/technical-analysis/scripts/ensure_yfinance_environment.sh"
fi

if [[ ! -x "$STAGING_ROOT/.venv/bin/python" ]]; then
  echo "uv did not create the package-local .venv" >&2
  exit 70
fi
"$STAGING_ROOT/.venv/bin/python" \
  "$STAGING_ROOT/scripts/verify_installed_package.py" --root "$STAGING_ROOT"
"$STAGING_ROOT/.venv/bin/python" \
  "$STAGING_ROOT/scripts/managed_package.py" write --root "$STAGING_ROOT"

if [[ -d "$TARGET_ROOT" ]]; then
  BACKUP_ROOT="$(mktemp -d "$TARGET_PARENT/.mars-package-backup.XXXXXX")"
  rmdir "$BACKUP_ROOT"
  mv "$TARGET_ROOT" "$BACKUP_ROOT"
fi
if ! mv "$STAGING_ROOT" "$TARGET_ROOT"; then
  echo "atomic package replacement failed" >&2
  exit 71
fi
if [[ -n "$BACKUP_ROOT" ]]; then
  rm -rf "$BACKUP_ROOT"
  BACKUP_ROOT=""
fi
trap - EXIT

echo "installed managed Mars Research Assistant package with 6 child Skills to $TARGET_ROOT"
