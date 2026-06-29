#!/bin/bash
# Build release archives for GitHub Releases (macOS source distribution).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VERSION="${1:-$(grep -E '^version = ' pyproject.toml | head -1 | sed 's/.*"\(.*\)".*/\1/')}"
DIST="$ROOT/dist"
PREFIX="agent-light-${VERSION}"
ZIP="$DIST/${PREFIX}-macos.zip"
TAR="$DIST/${PREFIX}-macos.tar.gz"

mkdir -p "$DIST"
rm -f "$ZIP" "$TAR"

echo "Building release ${VERSION}..."

git archive --format=zip --prefix="${PREFIX}/" -o "$ZIP" HEAD
git archive --format=tar.gz --prefix="${PREFIX}/" -o "$TAR" HEAD

echo "✓ $ZIP"
echo "✓ $TAR"
echo ""
echo "Upload with:"
echo "  gh release create v${VERSION} \"$ZIP\" \"$TAR\" --title \"v${VERSION}\" --notes \"...\""
