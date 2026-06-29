#!/bin/bash
# Build release archives for GitHub Releases.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VERSION="${1:-$(grep -E '^version = ' pyproject.toml | head -1 | sed 's/.*"\(.*\)".*/\1/')}"
DIST="$ROOT/dist"
PREFIX="agent-light-${VERSION}"
SRC_ZIP="$DIST/${PREFIX}-macos-source.zip"
SRC_TAR="$DIST/${PREFIX}-macos-source.tar.gz"
APP_ZIP="$DIST/${PREFIX}-macos-app.zip"

mkdir -p "$DIST"

echo "==> Source archives (${VERSION})"
rm -f "$SRC_ZIP" "$SRC_TAR"
git archive --format=zip --prefix="${PREFIX}/" -o "$SRC_ZIP" HEAD
git archive --format=tar.gz --prefix="${PREFIX}/" -o "$SRC_TAR" HEAD
echo "✓ $SRC_ZIP"
echo "✓ $SRC_TAR"

echo ""
echo "==> Standalone app (${VERSION})"
chmod +x scripts/build-app.sh
./scripts/build-app.sh "$VERSION"

echo ""
echo "Release assets:"
ls -lh "$SRC_ZIP" "$SRC_TAR" "$APP_ZIP"
