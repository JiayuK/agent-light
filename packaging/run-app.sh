#!/bin/bash
# Launch the bundled Agent Light.app (no Python / pip required).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="$SCRIPT_DIR/Agent Light.app"
MACOS="$APP/Contents/MacOS"
PID_FILE="$HOME/.agent-light/agent-light.pid"
LOG_FILE="$HOME/.agent-light/logs/agent-light.log"

if [[ ! -d "$APP" ]]; then
  echo "✗ 未找到 Agent Light.app，请确认已解压完整发布包"
  exit 1
fi

if [[ "${1:-}" == "stop" ]]; then
  if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
      mkdir -p "$HOME/.agent-light"
      echo stop > "$HOME/.agent-light/shutdown.request"
      kill -TERM "$PID" 2>/dev/null || true
      echo "✓ 已发送停止请求 (PID $PID)"
      for _ in 1 2 3 4 5 6; do
        kill -0 "$PID" 2>/dev/null || { echo "✓ Agent Light 已关闭"; rm -f "$HOME/.agent-light/shutdown.request"; exit 0; }
        sleep 0.5
      done
      echo "⚠ 进程未响应，强制终止..."
      kill -9 "$PID" 2>/dev/null || true
      rm -f "$PID_FILE" "$HOME/.agent-light/shutdown.request"
    else
      echo "进程 $PID 已不存在，清理 PID 文件"
      rm -f "$PID_FILE"
    fi
  else
    echo "Agent Light 未在运行"
  fi
  exit 0
fi

if [[ "${1:-}" == "status" ]]; then
  if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "✓ Agent Light 运行中 (PID $(cat "$PID_FILE"))"
    if [[ -f "$LOG_FILE" ]]; then
      echo "  日志: $LOG_FILE"
    else
      echo "  日志: 未启用（默认静默；使用 ./run-app.sh verbose 可写日志）"
    fi
  else
    echo "✗ Agent Light 未运行"
  fi
  exit 0
fi

if [[ "${1:-}" == "install-hooks" || "${1:-}" == "install-cursor-hooks" ]]; then
  exec "$MACOS/agent-light-hooks"
fi

if [[ "${1:-}" == "uninstall-hooks" ]]; then
  exec "$MACOS/agent-light-hooks" --uninstall
fi

if [[ "${1:-}" == "paths" ]]; then
  exec "$MACOS/agent-light-hooks" --paths
fi

VERBOSE_ARGS=()
if [[ "${1:-}" == "verbose" || "${1:-}" == "--verbose" || "${1:-}" == "-v" ]]; then
  VERBOSE_ARGS=(--verbose)
  shift
fi

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "Agent Light 已在运行 (PID $(cat "$PID_FILE"))"
  echo "  停止: ./run-app.sh stop"
  echo "  状态: ./run-app.sh status"
  exit 0
fi

check_accessibility() {
  osascript -e 'tell application "System Events" to return name of first process' >/dev/null 2>&1
}

if ! check_accessibility 2>/dev/null; then
  echo "⚠️  需要辅助功能权限 (Accessibility)"
  echo "   系统设置 → 隐私与安全性 → 辅助功能 → 添加 Terminal"
  open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility" 2>/dev/null || true
fi

if [[ ${#VERBOSE_ARGS[@]} -gt 0 ]]; then
  echo "启动 Agent Light（日志模式）..."
  echo "  关闭: ./run-app.sh stop  |  菜单栏图标 → 退出"
  echo "  日志: $LOG_FILE"
  echo ""
  exec "$MACOS/Agent Light" "${VERBOSE_ARGS[@]}" "$@"
fi

nohup "$MACOS/Agent Light" --quiet "$@" > /dev/null 2>&1 &
sleep 1.0
if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "✓ Agent Light 已启动 (PID $(cat "$PID_FILE"))"
  echo "  停止: ./run-app.sh stop"
  echo "  状态: ./run-app.sh status"
  echo "  调试: ./run-app.sh verbose"
else
  echo "✗ 启动失败，请运行 ./run-app.sh verbose 查看错误信息"
  exit 1
fi
