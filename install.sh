#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
INSTALL_DESKTOP=1
INSTALL_DEV=0
INSTALL_SYSTEM_DEPS=0

usage() {
  cat <<USAGE
Frost Authenticator installer

Usage:
  ./install.sh [options]

Options:
  --system-deps   Install Ubuntu system packages with sudo apt-get first.
  --dev           Install development/test extras.
  --no-desktop    Do not install the desktop launcher.
  -h, --help      Show this help.

Environment:
  PYTHON_BIN=python3.12   Override Python executable.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --system-deps) INSTALL_SYSTEM_DEPS=1 ;;
    --dev) INSTALL_DEV=1 ;;
    --no-desktop) INSTALL_DESKTOP=0 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

cd "$ROOT"

if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  if [[ "${ID:-}" == "ubuntu" && "${VERSION_ID:-}" != "24.04" ]]; then
    echo "提示：推荐环境是 Ubuntu 24.04 LTS；当前是 ${PRETTY_NAME:-unknown}。继续安装。"
  fi
fi

if [[ "$INSTALL_SYSTEM_DEPS" -eq 1 ]]; then
  if ! command -v apt-get >/dev/null 2>&1; then
    echo "--system-deps 只支持 apt-get 系统。" >&2
    exit 1
  fi
  sudo apt-get update
  sudo apt-get install -y \
    python3.12 python3.12-venv python3-pip \
    libxcb-cursor0 libxkbcommon-x11-0 libegl1 libgl1
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  cat >&2 <<MSG
找不到 $PYTHON_BIN。
Ubuntu 24.04 推荐先运行：
  sudo apt update
  sudo apt install -y python3.12 python3.12-venv python3-pip libxcb-cursor0 libxkbcommon-x11-0 libegl1 libgl1

或者直接：
  ./install.sh --system-deps
MSG
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info[:2] != (3, 12):
    raise SystemExit(f"需要 Python 3.12，当前是 {sys.version.split()[0]}")
PY

create_venv() {
  echo "创建 .venv ..."
  rm -rf .venv
  if "$PYTHON_BIN" -m venv .venv; then
    return 0
  fi

  echo "python -m venv 失败；尝试 virtualenv 备用路径。"
  rm -rf .venv
  if "$PYTHON_BIN" -m virtualenv .venv; then
    return 0
  fi

  cat >&2 <<MSG
无法创建 .venv。Ubuntu 24.04 通常需要：
  sudo apt update
  sudo apt install -y python3.12-venv

然后重新运行：
  ./install.sh
MSG
  return 1
}

if [[ -x .venv/bin/python ]]; then
  if ! .venv/bin/python - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)
PY
  then
    echo "现有 .venv 不是 Python 3.12，重建。"
    create_venv
  fi
else
  create_venv
fi

.venv/bin/python -m pip install --upgrade pip setuptools wheel
if [[ "$INSTALL_DEV" -eq 1 ]]; then
  .venv/bin/python -m pip install -e '.[dev]'
else
  .venv/bin/python -m pip install -e .
fi

if [[ "$INSTALL_DESKTOP" -eq 1 ]]; then
  ./scripts/install_desktop.sh
fi

cat <<DONE

安装完成。
运行：
  ./run.sh

保险库默认位置：
  ~/.local/share/frost-authenticator/vault.json
DONE
