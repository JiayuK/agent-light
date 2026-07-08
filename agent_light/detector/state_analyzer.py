"""Analyze AI tool instance states (running / waiting / idle) via agent hooks."""

from __future__ import annotations

import logging
import re
import time

from ..models import LightState, MonitoredInstance
from .window_api import collect_window_text, get_app_windows
from .claude_desktop_hook_monitor import analyze_claude_desktop_hooks
from .cli_hook_monitor import analyze_cli_hooks
from .cursor_hook_monitor import analyze_cursor_hooks

logger = logging.getLogger(__name__)

WAITING_PATTERNS = [
    r"\baccept\b",
    r"\breject\b",
    r"\bapprove\b",
    r"\bconfirm\b",
    r"needs? (your )?approval",
    r"waiting for (your )?(confirmation|approval|review|input)",
    r"确认",
    r"等待确认",
]

RUNNING_PATTERNS = [
    r"generating",
    r"thinking",
    r"streaming",
    r"生成中",
    r"思考中",
]

WAITING_RE = [re.compile(p, re.IGNORECASE) for p in WAITING_PATTERNS]
RUNNING_RE = [re.compile(p, re.IGNORECASE) for p in RUNNING_PATTERNS]

_HOOK_STATUS_TTL_SEC = 5.0
_hook_status_cache_at = 0.0
_hook_status_cache: dict[str, bool] = {}


def _hook_install_status() -> dict[str, bool]:
    global _hook_status_cache_at
    now = time.time()
    if _hook_status_cache and now - _hook_status_cache_at <= _HOOK_STATUS_TTL_SEC:
        return dict(_hook_status_cache)
    try:
        from ..agent_hooks import hooks_install_status

        status = hooks_install_status()
    except Exception as exc:
        logger.debug("Failed to read hook install status: %s", exc)
        status = {}
    _hook_status_cache.clear()
    _hook_status_cache.update({str(k): bool(v) for k, v in status.items()})
    _hook_status_cache_at = now
    return dict(_hook_status_cache)


def _hook_status_key(tool_name: str) -> str:
    if tool_name in ("claude-code", "claude-desktop"):
        return "claude"
    return tool_name


def _hook_warning_reason(tool_name: str) -> str:
    labels = {
        "cursor": "Cursor",
        "codex": "Codex",
        "claude-code": "Claude Code",
        "claude-desktop": "Claude Code",
    }
    label = labels.get(tool_name, tool_name)
    return f"hook: {label} Hook 未安装或配置不完整，请在菜单栏安装 Hook 并重启工具"


def _apply_hook_warning_if_needed(instance: MonitoredInstance) -> bool:
    status = _hook_install_status()
    if status.get(_hook_status_key(instance.tool_name), False):
        return False
    instance.state = LightState.WAITING
    instance.state_reason = _hook_warning_reason(instance.tool_name)
    return True


def _match_patterns(text: str, patterns: list[re.Pattern[str]]) -> str | None:
    for pat in patterns:
        m = pat.search(text)
        if m:
            return m.group(0)
    return None


def _apply_hook_state(
    instance: MonitoredInstance,
    hook_state: LightState | None,
    hook_reason: str,
) -> MonitoredInstance:
    if hook_state is not None:
        instance.state = hook_state
        instance.state_reason = hook_reason
    else:
        instance.state = LightState.IDLE
        instance.state_reason = "hook: idle"
    return instance


def _analyze_cursor_instance(instance: MonitoredInstance) -> MonitoredInstance:
    if _apply_hook_warning_if_needed(instance):
        return instance
    workspace = str(instance.extra.get("workspace") or instance.extra.get("project") or "")
    window_key = instance.extra.get("window_key")
    hook_state, hook_reason = analyze_cursor_hooks(
        workspace, str(window_key) if window_key else None
    )
    return _apply_hook_state(instance, hook_state, hook_reason)


def _analyze_cli_instance(instance: MonitoredInstance) -> MonitoredInstance:
    if _apply_hook_warning_if_needed(instance):
        return instance
    cwd = str(instance.extra.get("cwd") or "")
    hook_state, hook_reason = analyze_cli_hooks(instance.tool_name, cwd)
    return _apply_hook_state(instance, hook_state, hook_reason)


def _analyze_claude_desktop_instance(instance: MonitoredInstance) -> MonitoredInstance:
    cwd = str(instance.extra.get("cwd") or instance.extra.get("workspace") or "")
    session_id = instance.extra.get("cli_session_id") or instance.extra.get("session_id")
    session_text = str(session_id).strip() if session_id else None

    if cwd:
        if _apply_hook_warning_if_needed(instance):
            return instance
        hook_state, hook_reason = analyze_claude_desktop_hooks(cwd, session_text)
        return _apply_hook_state(instance, hook_state, hook_reason)

    return _analyze_gui_instance(instance, estimate_only=True)


def _analyze_gui_instance(
    instance: MonitoredInstance,
    *,
    estimate_only: bool = False,
) -> MonitoredInstance:
    if instance.tool_name == "cursor":
        return _analyze_cursor_instance(instance)

    window = instance.extra.get("window")
    text = ""
    if window is not None:
        text = collect_window_text(instance.pid, window)
    else:
        windows = get_app_windows(instance.pid)
        idx = instance.window_id or 0
        if windows and idx < len(windows):
            text = collect_window_text(instance.pid, windows[idx])

    waiting_hit = _match_patterns(text, WAITING_RE)
    if waiting_hit:
        instance.state = LightState.WAITING
        prefix = "UI (估算): " if estimate_only else "UI: "
        instance.state_reason = f"{prefix}{waiting_hit}"
        return instance

    running_hit = _match_patterns(text, RUNNING_RE)
    if running_hit:
        instance.state = LightState.RUNNING
        prefix = "UI (估算): " if estimate_only else "UI: "
        instance.state_reason = f"{prefix}{running_hit}"
        return instance

    instance.state = LightState.IDLE
    if estimate_only:
        instance.state_reason = "desktop: 非编程模式（无 Hook）"
    else:
        instance.state_reason = "idle"
    return instance


def analyze_states(instances: list[MonitoredInstance]) -> list[MonitoredInstance]:
    result: list[MonitoredInstance] = []
    for inst in instances:
        try:
            if inst.tool_name in ("codex", "claude-code"):
                result.append(_analyze_cli_instance(inst))
            elif inst.tool_name == "claude-desktop":
                result.append(_analyze_claude_desktop_instance(inst))
            else:
                result.append(_analyze_gui_instance(inst))
        except Exception as exc:
            logger.debug("State analysis failed for %s: %s", inst.instance_id, exc)
            inst.state = LightState.IDLE
            inst.state_reason = "unknown"
            result.append(inst)
    return result
