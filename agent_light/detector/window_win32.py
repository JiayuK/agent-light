"""Win32 window enumeration and focus (x64 Windows only)."""

from __future__ import annotations

import ctypes
import logging
from ctypes import wintypes
from typing import Any

logger = logging.getLogger(__name__)

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

SW_RESTORE = 9


def _enum_windows_for_pid(pid: int) -> list[int]:
    hwnds: list[int] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def callback(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        proc_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc_id))
        if proc_id.value == pid:
            hwnds.append(hwnd)
        return True

    user32.EnumWindows(callback, 0)
    return hwnds


def get_app_windows(pid: int) -> list[int]:
    return _enum_windows_for_pid(pid)


def get_window_title(window: Any) -> str:
    hwnd = int(window)
    length = user32.GetWindowTextLengthW(hwnd) + 1
    if length <= 1:
        return ""
    buf = ctypes.create_unicode_buffer(length)
    user32.GetWindowTextW(hwnd, buf, length)
    return buf.value or ""


def collect_text_from_element(_element: Any, depth: int = 0, max_depth: int = 12) -> list[str]:
    return []


def collect_window_text(pid: int, window: Any) -> str:
    return get_window_title(window)


def focus_window(pid: int, window: Any) -> bool:
    hwnd = int(window)
    try:
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception as exc:
        logger.debug("focus_window failed pid=%s hwnd=%s: %s", pid, hwnd, exc)
        return False


def focus_process(pid: int) -> bool:
    hwnds = get_app_windows(pid)
    if not hwnds:
        return False
    return focus_window(pid, hwnds[0])
