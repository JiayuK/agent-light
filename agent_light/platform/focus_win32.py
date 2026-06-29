"""Windows x64 focus helpers."""

from __future__ import annotations

import logging
from pathlib import Path, PureWindowsPath

import psutil

from ..detector.process_scanner import scan_instances
from ..detector.window_api import focus_process, focus_window, get_app_windows, get_window_title
from ..models import MonitoredInstance

logger = logging.getLogger(__name__)

CURSOR_EXE = "cursor.exe"


def _match_terms(instance: MonitoredInstance) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()

    def add(raw: str) -> None:
        text = raw.strip()
        if not text:
            return
        key = text.lower()
        if key in seen:
            return
        seen.add(key)
        terms.append(text)

    window_title = instance.extra.get("window_title")
    if isinstance(window_title, str):
        add(window_title)

    for key in ("project",):
        value = instance.extra.get(key)
        if isinstance(value, str):
            add(value)

    workspace = instance.extra.get("workspace")
    if isinstance(workspace, str) and workspace:
        add(PureWindowsPath(workspace).name)

    if " · " in instance.display_name:
        add(instance.display_name.split(" · ")[-1])

    cwd = instance.extra.get("cwd")
    if isinstance(cwd, str) and cwd:
        add(PureWindowsPath(cwd).name)

    terms.sort(key=len, reverse=True)
    return terms


def _find_cursor_pid() -> int:
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if (proc.info.get("name") or "").lower() == CURSOR_EXE:
                return int(proc.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
            continue
    return 0


def _find_cursor_window(pid: int, terms: list[str]):
    if not terms:
        return None
    lowered = [term.lower() for term in terms]
    for hwnd in get_app_windows(pid):
        title = (get_window_title(hwnd) or "").lower()
        if any(term in title for term in lowered):
            return hwnd
    return None


def focus_cursor_instance(instance: MonitoredInstance) -> bool:
    terms = _match_terms(instance)
    pid = instance.pid or _find_cursor_pid()

    window = instance.extra.get("window")
    if window is not None and pid and focus_window(pid, window):
        return True

    if pid:
        matched = _find_cursor_window(pid, terms)
        if matched is not None and focus_window(pid, matched):
            return True

    if pid and focus_process(pid):
        return True

    return False


def focus_cli_instance(instance: MonitoredInstance) -> bool:
    terminal_pid = instance.extra.get("terminal_pid")
    if terminal_pid and focus_process(int(terminal_pid)):
        return True
    shell_pid = instance.extra.get("shell_pid")
    if shell_pid and focus_process(int(shell_pid)):
        return True
    return focus_process(instance.pid)


def focus_gui_instance(instance: MonitoredInstance) -> bool:
    window = instance.extra.get("window")
    if window is not None and focus_window(instance.pid, window):
        return True

    windows = get_app_windows(instance.pid)
    idx = instance.window_id
    if windows and idx is not None and 0 <= idx < len(windows):
        return focus_window(instance.pid, windows[idx])

    return focus_process(instance.pid)


def _resolve_instance(instance: MonitoredInstance) -> MonitoredInstance:
    try:
        for fresh in scan_instances():
            if fresh.instance_id == instance.instance_id:
                return fresh
    except Exception as exc:
        logger.debug("Failed to refresh instance before focus: %s", exc)
    return instance


def focus_instance(instance: MonitoredInstance) -> None:
    target = _resolve_instance(instance)
    logger.info("Focus requested: %s", target.display_name)
    try:
        if target.tool_name == "cursor":
            ok = focus_cursor_instance(target)
        elif target.tool_name in ("codex", "claude-code"):
            ok = focus_cli_instance(target)
        else:
            ok = focus_gui_instance(target)
        logger.info("Focus result for %s: %s", target.display_name, ok)
    except Exception:
        logger.exception("Failed to focus %s", target.display_name)
