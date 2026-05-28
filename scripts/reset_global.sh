#!/usr/bin/env bash
set -euo pipefail

APP_ID="frost-authenticator"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_ROOT="${BACKUP_ROOT:-$HOME/.local/share/${APP_ID}-backups}"
BACKUP_DIR="$BACKUP_ROOT/reset-$STAMP"
KEEP_DESKTOP=0

usage() {
  cat <<USAGE
Frost Authenticator global reset

Usage:
  ./scripts/reset_global.sh [options]

Options:
  --keep-desktop   Keep the Ubuntu desktop launcher and icon.
  -h, --help       Show this help.

What it resets:
  - ~/.local/share/frost-authenticator
  - ~/.config/frost-authenticator
  - ~/.cache/frost-authenticator
  - ~/.local/share/applications/frost-authenticator.desktop
  - ~/.local/share/icons/hicolor/scalable/apps/frost-authenticator.svg

Safety:
  Existing app data is moved to a timestamped backup directory instead of being
  deleted. The backup root is:
    $BACKUP_ROOT
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep-desktop) KEEP_DESKTOP=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

move_if_exists() {
  local src="$1"
  local label="$2"
  if [[ -e "$src" || -L "$src" ]]; then
    mkdir -p "$BACKUP_DIR"
    mv "$src" "$BACKUP_DIR/$label"
    echo "moved: $src -> $BACKUP_DIR/$label"
    return 0
  fi
  echo "skip:  $src"
  return 1
}

copy_then_remove_file() {
  local src="$1"
  local label="$2"
  if [[ -e "$src" || -L "$src" ]]; then
    mkdir -p "$BACKUP_DIR/desktop"
    cp -a "$src" "$BACKUP_DIR/desktop/$label"
    rm -f "$src"
    echo "removed: $src  (backup: $BACKUP_DIR/desktop/$label)"
    return 0
  fi
  echo "skip:    $src"
  return 1
}

changed=0
move_if_exists "$HOME/.local/share/$APP_ID" "data" && changed=1 || true
move_if_exists "$HOME/.config/$APP_ID" "config" && changed=1 || true
move_if_exists "$HOME/.cache/$APP_ID" "cache" && changed=1 || true

if [[ "$KEEP_DESKTOP" -eq 0 ]]; then
  copy_then_remove_file "$HOME/.local/share/applications/$APP_ID.desktop" "$APP_ID.desktop" && changed=1 || true
  copy_then_remove_file "$HOME/.local/share/icons/hicolor/scalable/apps/$APP_ID.svg" "$APP_ID.svg" && changed=1 || true
  if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" || true
  fi
fi

if [[ "$changed" -eq 0 ]]; then
  echo "Global reset: already clean. No files changed."
else
  echo "Global reset complete. Backup directory: $BACKUP_DIR"
fi
