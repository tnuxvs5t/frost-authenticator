#!/usr/bin/env bash
set -euo pipefail
rm -f "$HOME/.local/share/applications/frost-authenticator.desktop"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/frost-authenticator.svg"
echo "已移除桌面启动器和图标。保险库未删除。"
