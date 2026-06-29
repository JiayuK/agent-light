"""Schedule callbacks on the UI main thread."""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any

from . import IS_DARWIN

_win_queue: list[tuple[Callable[..., Any], tuple, dict]] = []


def call_on_main_thread(func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    if IS_DARWIN:
        from PyObjCTools.AppHelper import callAfter

        callAfter(func, *args, **kwargs)
        return
    if sys.platform == "win32":
        _win_queue.append((func, args, kwargs))
        return
    func(*args, **kwargs)


def drain_win_queue() -> None:
    """Process pending callbacks (Windows tk/pystray loop)."""
    while _win_queue:
        func, args, kwargs = _win_queue.pop(0)
        try:
            func(*args, **kwargs)
        except Exception:
            import logging

            logging.getLogger(__name__).exception("main-thread callback failed")
