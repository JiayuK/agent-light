"""Traffic-light color presets and helpers (shared across platforms)."""

from __future__ import annotations

import re

from .models import LightState

HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")

DEFAULT_ON_COLORS: dict[str, str] = {
    LightState.RUNNING.value: "#ff2e26",
    LightState.WAITING.value: "#ffd100",
    LightState.IDLE.value: "#26e661",
}

STATE_LABELS: dict[LightState, str] = {
    LightState.RUNNING: "工作中（红灯）",
    LightState.WAITING: "待确认（黄灯）",
    LightState.IDLE: "空闲（绿灯）",
}

STATE_ORDER = (LightState.RUNNING, LightState.WAITING, LightState.IDLE)


def normalize_hex(value: str) -> str | None:
    value = value.strip()
    match = HEX_RE.match(value)
    if not match:
        return None
    return f"#{match.group(1).lower()}"


def parse_hex_rgb(value: str) -> tuple[int, int, int] | None:
    normalized = normalize_hex(value)
    if not normalized:
        return None
    raw = normalized[1:]
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


def dim_hex(value: str, factor: float = 0.55) -> str:
    rgb = parse_hex_rgb(value)
    if rgb is None:
        return value
    r, g, b = rgb
    return rgb_to_hex(int(r * factor), int(g * factor), int(b * factor))


def default_on_colors() -> dict[str, str]:
    return dict(DEFAULT_ON_COLORS)


def sanitize_on_colors(raw: dict[str, str] | None) -> dict[str, str]:
    colors = default_on_colors()
    if not raw:
        return colors
    for state in STATE_ORDER:
        value = raw.get(state.value)
        if value is None:
            continue
        normalized = normalize_hex(str(value))
        if normalized:
            colors[state.value] = normalized
    return colors


def color_pairs_from_on(on_colors: dict[str, str]) -> dict[LightState, tuple[str, str]]:
    sanitized = sanitize_on_colors(on_colors)
    return {
        state: (sanitized[state.value], dim_hex(sanitized[state.value]))
        for state in STATE_ORDER
    }
