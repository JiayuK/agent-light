"""Map Cursor window index to active agent conversation IDs from hook logs."""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path

from .cursor_log_utils import latest_session_dir, iter_window_log_dirs, read_log_tail

logger = logging.getLogger(__name__)

CONVERSATION_ID_RE = re.compile(
    r'"conversation_id"\s*:\s*"([0-9a-fA-F-]{36})"',
)

_CACHE_TTL_SEC = 5.0
_cache: dict[str, tuple[float, list[str]]] = {}


def recent_conversation_ids_for_window(window_key: str) -> list[str]:
    """
    Return conversation IDs seen recently in this window's hook logs,
    most recently active first.
    """
    window_key = str(window_key or "").strip()
    if not window_key:
        return []

    now = time.time()
    cached = _cache.get(window_key)
    if cached and now - cached[0] <= _CACHE_TTL_SEC:
        return cached[1]

    ids = _load_conversation_ids(window_key)
    _cache[window_key] = (now, ids)
    return ids


def invalidate_conversation_cache() -> None:
    _cache.clear()


def _load_conversation_ids(window_key: str) -> list[str]:
    session = latest_session_dir()
    if not session:
        return []

    hooks_logs: list[Path] = []
    for window_dir in iter_window_log_dirs(session, window_key):
        hooks_logs.extend(window_dir.glob("output_*/cursor.hooks.*.log"))

    if not hooks_logs:
        return []

    hooks_log = max(hooks_logs, key=lambda p: p.stat().st_mtime)
    try:
        tail = read_log_tail(hooks_log, max_bytes=65536)
    except OSError as exc:
        logger.debug("Failed to read hooks log %s: %s", hooks_log, exc)
        return []

    matches = CONVERSATION_ID_RE.findall(tail)
    ordered: list[str] = []
    seen: set[str] = set()
    for conversation_id in reversed(matches):
        if conversation_id in seen:
            continue
        seen.add(conversation_id)
        ordered.append(conversation_id)
    return ordered
