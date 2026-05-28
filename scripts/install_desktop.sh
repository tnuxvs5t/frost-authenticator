#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
DESKTOP_FILE="$APP_DIR/frost-authenticator.desktop"
ICON_FILE="$ICON_DIR/frost-authenticator.svg"

mkdir -p "$APP_DIR" "$ICON_DIR"
cp "$ROOT/assets/frost-authenticator.svg" "$ICON_FILE"

cat > "$DESKTOP_FILE" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Frost Authenticator
Comment=Local encrypted TOTP authenticator
Exec=$ROOT/run.sh
Icon=frost-authenticator
Terminal=false
Categories=Utility;Security;
StartupNotify=true
DESKTOP

chmod +x "$DESKTOP_FILE"
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APP_DIR" || true
fi

echo "已安装桌面启动器：$DESKTOP_FILE"
