#!/bin/bash
# Build standalone Agent Light.app (PyInstaller) and release zip.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VERSION="${1:-$(grep -E '^version = ' pyproject.toml | head -1 | sed 's/.*"\(.*\)".*/\1/')}"
DIST="$ROOT/dist"
STAGE="$DIST/agent-light-${VERSION}-macos-app"
APP_ZIP="$DIST/agent-light-${VERSION}-macos-app.zip"

PYTHON=""
for candidate in python3.12 python3.11 python3.10 python3.9 python3; do
  if command -v "$candidate" >/dev/null 2>&1 \
    && "$candidate" -c 'import sys; exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
    PYTHON="$candidate"
    break
  fi
done

if [[ -z "$PYTHON" ]]; then
  echo "✗ 未找到 Python 3.9+"
  exit 1
fi

echo "Building Agent Light.app ${VERSION} with $PYTHON ..."

if ! "$PYTHON" -c "import PyInstaller" 2>/dev/null; then
  echo "安装构建依赖 PyInstaller ..."
  "$PYTHON" -m pip install --upgrade pip setuptools wheel -q
  "$PYTHON" -m pip install pyinstaller -q
  "$PYTHON" -m pip install -e . -q
else
  "$PYTHON" -m pip install -e . -q
fi

rm -rf "$ROOT/build" "$DIST/Agent Light.app" "$STAGE" "$APP_ZIP"
"$PYTHON" -m PyInstaller packaging/agent-light.spec --noconfirm --clean

if [[ ! -d "$DIST/Agent Light.app" ]]; then
  echo "✗ 构建失败：未生成 dist/Agent Light.app"
  exit 1
fi

mkdir -p "$STAGE"
cp -R "$DIST/Agent Light.app" "$STAGE/"
cp packaging/run-app.sh "$STAGE/"
chmod +x "$STAGE/run-app.sh"

(
  cd "$DIST"
  rm -f "$(basename "$APP_ZIP")"
  ditto -c -k --sequesterRsrc --keepParent "$(basename "$STAGE")" "$(basename "$APP_ZIP")"
)

echo "✓ $APP_ZIP"
du -sh "$APP_ZIP" "$DIST/Agent Light.app"
