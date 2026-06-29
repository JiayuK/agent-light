"""Platform detection and shared helpers."""

from __future__ import annotations

import sys

IS_DARWIN = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"


def platform_name() -> str:
    if IS_DARWIN:
        return "darwin"
    if IS_WINDOWS:
        return "win32"
    return sys.platform
