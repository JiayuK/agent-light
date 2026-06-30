"""User preferences (persisted)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .constants import APP_DATA_DIR
from .traffic_colors import default_on_colors, sanitize_on_colors

logger = logging.getLogger(__name__)

SETTINGS_DIR = APP_DATA_DIR
SETTINGS_FILE = SETTINGS_DIR / "settings.json"

# display_mode: "traffic" | "kun" | "custom:{style_id}"
_display_mode = "traffic"
_tool_paths: dict[str, str] = {}
_traffic_on_colors: dict[str, str] = default_on_colors()
_hooks_reminder_dismissed = False
_loaded = False


def _load() -> None:
    global _display_mode, _tool_paths, _traffic_on_colors, _hooks_reminder_dismissed, _loaded
    if _loaded:
        return
    try:
        if SETTINGS_FILE.exists():
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if "display_mode" in data:
                _display_mode = str(data["display_mode"])
            elif data.get("kun_mode"):
                _display_mode = "kun"
            else:
                _display_mode = "traffic"
            raw_paths = data.get("tool_paths", {})
            if isinstance(raw_paths, dict):
                _tool_paths = {
                    str(k): str(v)
                    for k, v in raw_paths.items()
                    if isinstance(k, str) and isinstance(v, str) and v.strip()
                }
            raw_colors = data.get("traffic_on_colors")
            if isinstance(raw_colors, dict):
                _traffic_on_colors = sanitize_on_colors(
                    {str(k): str(v) for k, v in raw_colors.items() if isinstance(k, str) and isinstance(v, str)}
                )
            if "hooks_reminder_dismissed" in data:
                _hooks_reminder_dismissed = bool(data["hooks_reminder_dismissed"])
    except (OSError, json.JSONDecodeError) as exc:
        logger.debug("Failed to load settings: %s", exc)
    _loaded = True


def _save() -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "display_mode": _display_mode,
        "hooks_reminder_dismissed": _hooks_reminder_dismissed,
        "traffic_on_colors": dict(_traffic_on_colors),
    }
    if _tool_paths:
        payload["tool_paths"] = dict(_tool_paths)
    SETTINGS_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def get_display_mode() -> str:
    _load()
    return _display_mode


def set_display_mode(mode: str) -> None:
    global _display_mode
    _load()
    _display_mode = mode
    _save()


def get_tool_paths() -> dict[str, str]:
    _load()
    return dict(_tool_paths)


def get_hooks_reminder_dismissed() -> bool:
    _load()
    return _hooks_reminder_dismissed


def set_hooks_reminder_dismissed(dismissed: bool) -> None:
    global _hooks_reminder_dismissed
    _load()
    _hooks_reminder_dismissed = dismissed
    _save()


def get_traffic_on_colors() -> dict[str, str]:
    _load()
    return dict(_traffic_on_colors)


def set_traffic_on_colors(colors: dict[str, str]) -> None:
    global _traffic_on_colors
    _load()
    _traffic_on_colors = sanitize_on_colors(colors)
    _save()


def reset_traffic_on_colors() -> None:
    global _traffic_on_colors
    _load()
    _traffic_on_colors = default_on_colors()
    _save()
