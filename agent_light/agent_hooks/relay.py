"""Agent hook relay — read JSON from stdin, write Agent Light state signals."""

from __future__ import annotations

import json
import logging
import os
import sys

from ..shutdown import is_agent_light_running
from .state_map import map_hook_event
from .store import write_signal

logger = logging.getLogger(__name__)

VALID_TOOLS = frozenset({"cursor", "codex", "claude-code"})


def _resolve_tool() -> str:
    tool = os.environ.get("AGENT_LIGHT_TOOL", "cursor").strip().lower()
    if tool == "claude":
        return "claude-code"
    return tool if tool in VALID_TOOLS else "cursor"


def run_relay() -> int:
    try:
        if not is_agent_light_running():
            print("{}")
            return 0

        try:
            payload = json.load(sys.stdin)
        except json.JSONDecodeError:
            print("{}")
            return 0

        if not isinstance(payload, dict):
            print("{}")
            return 0

        tool_name = _resolve_tool()
        event = str(
            payload.get("hook_event_name")
            or payload.get("hookEventName")
            or ""
        )
        state, reason = map_hook_event(event, payload)
        if state is not None:
            write_signal(tool_name, payload, state, reason)
    except Exception as exc:
        logger.debug("Hook relay skipped: %s", exc)

    print("{}")
    return 0


def main() -> None:
    raise SystemExit(run_relay())


if __name__ == "__main__":
    main()
