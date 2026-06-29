"""Runtime paths for development installs and frozen app bundles."""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def bundle_macos_dir() -> Path | None:
    """Contents/MacOS when running inside a frozen macOS .app bundle."""
    if not is_frozen():
        return None
    macos = Path(sys.executable).resolve().parent
    if macos.name == "MacOS" and macos.parent.name == "Contents":
        return macos
    return None


def relay_executable() -> Path | None:
    """CLI entry used by installed agent hooks to relay events."""
    bundle = bundle_macos_dir()
    if bundle is not None:
        candidate = bundle / "agent-light-relay"
        if candidate.is_file():
            return candidate
    return None


def hooks_cli_executable() -> Path | None:
    """CLI for install/uninstall hooks from a bundled release."""
    bundle = bundle_macos_dir()
    if bundle is not None:
        candidate = bundle / "agent-light-hooks"
        if candidate.is_file():
            return candidate
    return None


def python_for_hooks() -> str:
    """Interpreter path recorded for hook wrapper scripts."""
    return sys.executable
