"""Platform window API facade (macOS AX vs Windows Win32)."""

from __future__ import annotations

import sys
from typing import Any

if sys.platform == "darwin":
    from .ax_api import (
        collect_text_from_element,
        collect_window_text,
        focus_process,
        focus_window,
        get_app_windows,
        get_window_title,
    )
elif sys.platform == "win32":
    from .window_win32 import (
        collect_text_from_element,
        collect_window_text,
        focus_process,
        focus_window,
        get_app_windows,
        get_window_title,
    )
else:
    def get_app_windows(pid: int) -> list[Any]:
        return []

    def get_window_title(window: Any) -> str:
        return ""

    def collect_text_from_element(element: Any, depth: int = 0, max_depth: int = 12) -> list[str]:
        return []

    def collect_window_text(pid: int, window: Any) -> str:
        return ""

    def focus_window(pid: int, window: Any) -> bool:
        return False

    def focus_process(pid: int) -> bool:
        return False

__all__ = [
    "collect_text_from_element",
    "collect_window_text",
    "focus_process",
    "focus_window",
    "get_app_windows",
    "get_window_title",
]
