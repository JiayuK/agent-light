"""Windows default paths for Cursor / Claude / Codex."""

from __future__ import annotations

import os
from pathlib import Path


def appdata_roaming() -> Path:
    return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))


def appdata_local() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))


def default_cursor_user_data_dirs() -> list[Path]:
    return [
        appdata_roaming() / "Cursor",
        appdata_roaming() / "Cursor Nightly",
    ]


def default_cursor_user_data_dir() -> Path:
    return default_cursor_user_data_dirs()[0]


def default_claude_desktop_sessions_dir() -> Path:
    return appdata_roaming() / "Claude" / "claude-code-sessions"


def home_from_user_data_dir(user_data_dir: Path) -> Path | None:
    """On Windows, user data under %APPDATA%\\Vendor maps to %USERPROFILE%."""
    try:
        roaming = appdata_roaming().resolve()
        resolved = user_data_dir.expanduser().resolve()
        if resolved.is_relative_to(roaming):
            return Path.home()
    except (OSError, ValueError):
        pass
    return None


def cursor_install_candidates() -> list[Path]:
    candidates = [
        appdata_local() / "Programs" / "cursor" / "Cursor.exe",
        Path.home() / "AppData" / "Local" / "Programs" / "Cursor" / "Cursor.exe",
    ]
    return candidates
