"""Scan running Cursor / Claude Desktop / CLI instances on Windows x64."""

from __future__ import annotations

import logging
import re
from pathlib import Path, PureWindowsPath
from typing import Any

import psutil

from ..models import MonitoredInstance
from .claude_desktop_sessions import match_session_for_window_title
from .cli_tool_scanner import scan_cli_instances
from .window_api import get_app_windows, get_window_title
from .workspace_resolver import resolve_workspace_path

logger = logging.getLogger(__name__)

CURSOR_EXE_NAMES = frozenset({"cursor.exe"})
CLAUDE_DESKTOP_EXE_NAMES = frozenset({"claude.exe"})

CURSOR_HOST_RE = re.compile(
    r"extension-host\s+(?:\([^)]+\)\s+)?(.+?)\s+\[(\d+)-",
    re.IGNORECASE,
)


def _short_title(title: str, max_len: int = 28) -> str:
    title = title.strip() or "Untitled"
    if len(title) <= max_len:
        return title
    return title[: max_len - 1] + "…"


def _parse_project_from_window_title(title: str) -> str:
    title = title.strip()
    if not title:
        return "Untitled"
    title = re.sub(r"\s*[-–—]\s*Cursor\s*$", "", title, flags=re.IGNORECASE)
    for sep in (" — ", " - ", " – "):
        if sep in title:
            parts = [p.strip() for p in title.split(sep) if p.strip()]
            if len(parts) >= 2:
                return parts[-1]
    return title


def _cursor_display_name(project: str) -> str:
    return f"Cursor · {_short_title(project)}"


def _find_pids_by_exe_names(exe_names: frozenset[str]) -> list[int]:
    pids: list[int] = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = (proc.info.get("name") or "").lower()
            if name in exe_names:
                pids.append(int(proc.info["pid"]))
        except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
            continue
    return pids


def _scan_cursor_via_extension_hosts(main_pid: int) -> list[MonitoredInstance]:
    windows: dict[str, dict[str, Any]] = {}

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = " ".join(proc.cmdline())
            if "extension-host" not in cmdline.lower():
                continue
            if "cursor" not in cmdline.lower():
                continue

            match = CURSOR_HOST_RE.search(cmdline)
            if not match:
                continue

            workspace = match.group(1).strip()
            window_key = match.group(2)
            is_agent = "agent-exec" in cmdline.lower()

            entry = windows.setdefault(
                window_key,
                {"workspace": "", "pids": [], "agent_exec_pid": None},
            )
            entry["pids"].append(proc.info["pid"])
            if is_agent:
                entry["agent_exec_pid"] = proc.info["pid"]
            if workspace.lower() != "empty":
                entry["workspace"] = workspace
            elif not entry["workspace"]:
                entry["workspace"] = workspace
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    instances: list[MonitoredInstance] = []
    for window_key, info in sorted(windows.items()):
        label = info["workspace"]
        workspace = resolve_workspace_path(label, window_key)
        project = PureWindowsPath(workspace).name if workspace else label
        instances.append(
            MonitoredInstance(
                instance_id=f"cursor-win-{window_key}",
                tool_name="cursor",
                display_name=_cursor_display_name(project),
                pid=main_pid,
                window_id=int(window_key) if window_key.isdigit() else None,
                extra={
                    "window_key": window_key,
                    "workspace": workspace,
                    "project": project,
                    "host_pids": info["pids"],
                    "agent_exec_pid": info["agent_exec_pid"],
                },
            )
        )
    return instances


def _scan_cursor_via_windows(main_pid: int) -> list[MonitoredInstance]:
    instances: list[MonitoredInstance] = []
    hwnds = get_app_windows(main_pid)
    for idx, hwnd in enumerate(hwnds):
        raw_title = get_window_title(hwnd) or f"Window {idx + 1}"
        label = _parse_project_from_window_title(raw_title)
        workspace = resolve_workspace_path(label)
        project = PureWindowsPath(workspace).name if workspace else label
        instances.append(
            MonitoredInstance(
                instance_id=f"cursor-win32-{main_pid}-{idx}",
                tool_name="cursor",
                display_name=_cursor_display_name(project),
                pid=main_pid,
                window_id=idx,
                extra={
                    "window": hwnd,
                    "window_title": raw_title,
                    "workspace": workspace,
                    "project": project,
                },
            )
        )
    return instances


def _scan_cursor() -> list[MonitoredInstance]:
    pids = _find_pids_by_exe_names(CURSOR_EXE_NAMES)
    if not pids:
        return []

    main_pid = pids[0]
    hosts = _scan_cursor_via_extension_hosts(main_pid)
    if hosts:
        hwnds = get_app_windows(main_pid)
        for inst in hosts:
            project = str(inst.extra.get("project") or "")
            if project and hwnds:
                project_lower = project.lower()
                for hwnd in hwnds:
                    title = get_window_title(hwnd) or ""
                    if project_lower in title.lower():
                        inst.extra["window"] = hwnd
                        inst.extra["window_title"] = title
                        break
        return hosts

    ax = _scan_cursor_via_windows(main_pid)
    if ax:
        return ax

    return [
        MonitoredInstance(
            instance_id=f"cursor-{main_pid}",
            tool_name="cursor",
            display_name="Cursor · Unknown",
            pid=main_pid,
            extra={"project": "Unknown"},
        )
    ]


def _claude_desktop_display_name(title: str, cwd: str) -> str:
    if cwd:
        folder = PureWindowsPath(cwd).name or title
        return f"Claude Desktop · {_short_title(folder)}"
    return f"Claude Desktop · {_short_title(title)}"


def _scan_claude_desktop() -> list[MonitoredInstance]:
    instances: list[MonitoredInstance] = []
    for pid in _find_pids_by_exe_names(CLAUDE_DESKTOP_EXE_NAMES):
        hwnds = get_app_windows(pid)
        if hwnds:
            for idx, hwnd in enumerate(hwnds):
                title = get_window_title(hwnd) or f"Window {idx + 1}"
                extra: dict[str, Any] = {
                    "window": hwnd,
                    "window_title": title,
                }
                display_name = f"Claude Desktop · {_short_title(title)}"
                session = match_session_for_window_title(title)
                cwd = session.cwd if session else ""
                if cwd:
                    extra["cwd"] = cwd
                    extra["workspace"] = cwd
                    extra["project"] = PureWindowsPath(cwd).name
                    extra["coding_session"] = True
                if session:
                    extra["session_id"] = session.session_id
                    extra["cli_session_id"] = session.cli_session_id
                    extra["session_title"] = session.title
                display_name = _claude_desktop_display_name(title, cwd)
                instances.append(
                    MonitoredInstance(
                        instance_id=f"claude-desktop-win32-{pid}-{idx}",
                        tool_name="claude-desktop",
                        display_name=display_name,
                        pid=pid,
                        window_id=idx,
                        extra=extra,
                    )
                )
        else:
            instances.append(
                MonitoredInstance(
                    instance_id=f"claude-desktop-{pid}",
                    tool_name="claude-desktop",
                    display_name="Claude Desktop",
                    pid=pid,
                )
            )
    return instances


def scan_instances() -> list[MonitoredInstance]:
    all_instances: list[MonitoredInstance] = []
    all_instances.extend(_scan_cursor())
    all_instances.extend(_scan_claude_desktop())
    all_instances.extend(scan_cli_instances())

    seen: set[str] = set()
    unique: list[MonitoredInstance] = []
    for inst in all_instances:
        if inst.instance_id not in seen:
            seen.add(inst.instance_id)
            unique.append(inst)

    logger.debug("scan_instances → %d instance(s): %s", len(unique), [i.display_name for i in unique])
    return unique
