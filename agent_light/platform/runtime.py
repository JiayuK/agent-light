"""Runtime paths for development installs and frozen bundles."""

from __future__ import annotations

import sys
from pathlib import Path

from . import IS_DARWIN, IS_WINDOWS


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def bundle_macos_dir() -> Path | None:
    if not is_frozen() or not IS_DARWIN:
        return None
    macos = Path(sys.executable).resolve().parent
    if macos.name == "MacOS" and macos.parent.name == "Contents":
        return macos
    return None


def bundle_win32_dir() -> Path | None:
    if not is_frozen() or not IS_WINDOWS:
        return None
    exe_dir = Path(sys.executable).resolve().parent
    return exe_dir if exe_dir.is_dir() else None


def relay_executable() -> Path | None:
    if IS_DARWIN:
        bundle = bundle_macos_dir()
        if bundle is not None:
            candidate = bundle / "agent-light-relay"
            if candidate.is_file():
                return candidate
    if IS_WINDOWS:
        bundle = bundle_win32_dir()
        if bundle is not None:
            for name in ("agent-light-relay.exe", "agent-light-relay"):
                candidate = bundle / name
                if candidate.is_file():
                    return candidate
    return None


def hooks_cli_executable() -> Path | None:
    if IS_DARWIN:
        bundle = bundle_macos_dir()
        if bundle is not None:
            candidate = bundle / "agent-light-hooks"
            if candidate.is_file():
                return candidate
    if IS_WINDOWS:
        bundle = bundle_win32_dir()
        if bundle is not None:
            for name in ("agent-light-hooks.exe", "agent-light-hooks"):
                candidate = bundle / name
                if candidate.is_file():
                    return candidate
    return None


def python_for_hooks() -> str:
    return sys.executable
