"""Shared helpers for reading Cursor log directories."""

from __future__ import annotations

from pathlib import Path

from ..tool_paths import get_cursor_log_roots


def latest_session_dir() -> Path | None:
    best: Path | None = None
    best_mtime = 0.0
    for log_root in get_cursor_log_roots():
        try:
            sessions = [p for p in log_root.iterdir() if p.is_dir()]
        except OSError:
            continue
        for session in sessions:
            try:
                mtime = session.stat().st_mtime
            except OSError:
                continue
            if mtime > best_mtime:
                best_mtime = mtime
                best = session
    return best


def iter_window_log_dirs(session: Path, window_key: str) -> list[Path]:
    """Return Cursor log dirs for a window index, including Agent Windows workbenches."""
    key = str(window_key or "").strip()
    if not key:
        return []

    dirs: list[Path] = []
    exact = session / f"window{key}"
    if exact.is_dir():
        dirs.append(exact)

    for path in sorted(session.glob(f"window{key}_wb*")):
        if path.is_dir():
            dirs.append(path)

    dirs.sort(
        key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
        reverse=True,
    )
    return dirs


def read_log_tail(path: Path, max_bytes: int = 8192) -> str:
    try:
        size = path.stat().st_size
        with open(path, "rb") as f:
            if size > max_bytes:
                f.seek(size - max_bytes)
            return f.read().decode("utf-8", errors="replace")
    except OSError:
        return ""
