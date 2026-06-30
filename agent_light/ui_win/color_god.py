"""Windows traffic-light color settings window."""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import colorchooser, messagebox
from typing import Callable

from ..models import LightState
from ..settings import get_traffic_on_colors, set_traffic_on_colors
from ..traffic_colors import STATE_LABELS, STATE_ORDER, color_pairs_from_on, default_on_colors, normalize_hex

logger = logging.getLogger(__name__)

WIN_W = 420
WIN_H = 340

_window: tk.Toplevel | None = None


def _position_near_pointer(win: tk.Toplevel, width: int, height: int) -> None:
    """Place the window near the mouse cursor, clamped to the screen."""
    try:
        px, py = win.winfo_pointerxy()
    except tk.TclError:
        px, py = 0, 0
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = px - 40
    y = py - 20
    x = max(0, min(x, screen_w - width))
    y = max(0, min(y, screen_h - height))
    win.geometry(f"{width}x{height}+{x}+{y}")


def show_color_god(on_change: Callable[[], None] | None = None, master: tk.Misc | None = None) -> None:
    global _window
    if _window is not None and _window.winfo_exists():
        _window.lift()
        return

    root = master
    if root is None:
        root = tk._default_root  # type: ignore[attr-defined]
    if root is None:
        root = tk.Tk()
        root.withdraw()

    win = tk.Toplevel(root)
    win.title("颜色の神")
    win.configure(bg="#f5f5f5")
    win.resizable(False, False)
    _window = win
    _position_near_pointer(win, WIN_W, WIN_H)

    draft: dict[str, str] = get_traffic_on_colors()
    swatches: dict[str, tk.Canvas] = {}
    hex_vars: dict[str, tk.StringVar] = {}
    preview_dots: dict[LightState, tk.Canvas] = {}

    tk.Label(
        win,
        text="为交通灯模式的三种状态选择颜色（默认红 / 黄 / 绿）",
        bg="#f5f5f5",
        font=("Segoe UI", 10),
        wraplength=380,
        justify="left",
    ).pack(anchor="w", padx=16, pady=(14, 8))

    form = tk.Frame(win, bg="#f5f5f5")
    form.pack(fill="x", padx=16, pady=4)

    def refresh_preview() -> None:
        pairs = color_pairs_from_on(draft)
        for state, canvas in preview_dots.items():
            on_hex, _off = pairs[state]
            canvas.delete("all")
            canvas.create_oval(2, 2, 26, 26, fill=on_hex, outline="#333")

    def apply_color(state_key: str, hex_value: str) -> None:
        normalized = normalize_hex(hex_value)
        if not normalized:
            messagebox.showwarning("无效颜色", f"请输入 #RRGGBB 格式的颜色值。", parent=win)
            hex_vars[state_key].set(draft[state_key])
            return
        draft[state_key] = normalized
        hex_vars[state_key].set(normalized)
        swatch = swatches[state_key]
        swatch.delete("all")
        swatch.create_rectangle(0, 0, 36, 24, fill=normalized, outline="#666")
        refresh_preview()

    def pick_color(state: LightState) -> None:
        key = state.value
        current = draft[key]
        result = colorchooser.askcolor(color=current, title=f"选择 {STATE_LABELS[state]}", parent=win)
        if result and result[1]:
            apply_color(key, result[1])

    for row, state in enumerate(STATE_ORDER):
        key = state.value
        tk.Label(form, text=STATE_LABELS[state], bg="#f5f5f5", font=("Segoe UI", 10)).grid(
            row=row, column=0, sticky="w", pady=6
        )
        swatch = tk.Canvas(form, width=36, height=24, bg="#f5f5f5", highlightthickness=1, highlightbackground="#999")
        swatch.grid(row=row, column=1, padx=(8, 4))
        swatches[key] = swatch

        tk.Button(form, text="选择…", command=lambda s=state: pick_color(s)).grid(row=row, column=2, padx=4)

        hex_var = tk.StringVar(value=draft[key])
        hex_vars[key] = hex_var
        entry = tk.Entry(form, textvariable=hex_var, width=10, font=("Consolas", 10))
        entry.grid(row=row, column=3, padx=(8, 0))
        entry.bind(
            "<Return>",
            lambda _e, k=key: apply_color(k, hex_vars[k].get()),
        )
        entry.bind(
            "<FocusOut>",
            lambda _e, k=key: apply_color(k, hex_vars[k].get()),
        )

    preview_frame = tk.Frame(win, bg="#f5f5f5")
    preview_frame.pack(anchor="w", padx=16, pady=(12, 4))
    tk.Label(preview_frame, text="预览", bg="#f5f5f5", font=("Segoe UI", 10, "bold")).pack(anchor="w")
    dots_row = tk.Frame(preview_frame, bg="#f5f5f5")
    dots_row.pack(anchor="w", pady=(6, 0))
    for state in STATE_ORDER:
        canvas = tk.Canvas(dots_row, width=28, height=28, bg="#f5f5f5", highlightthickness=0)
        canvas.pack(side="left", padx=(0, 12))
        preview_dots[state] = canvas

    for key in draft:
        swatches[key].create_rectangle(0, 0, 36, 24, fill=draft[key], outline="#666")
    refresh_preview()

    btn_row = tk.Frame(win, bg="#f5f5f5")
    btn_row.pack(fill="x", padx=16, pady=(16, 14))

    def on_reset() -> None:
        draft.update(default_on_colors())
        for key in draft:
            hex_vars[key].set(draft[key])
            swatches[key].delete("all")
            swatches[key].create_rectangle(0, 0, 36, 24, fill=draft[key], outline="#666")
        refresh_preview()

    def on_save() -> None:
        for key in draft:
            normalized = normalize_hex(hex_vars[key].get())
            if not normalized:
                messagebox.showwarning("无效颜色", f"{STATE_LABELS[LightState(key)]} 的颜色格式无效。", parent=win)
                return
            draft[key] = normalized
        set_traffic_on_colors(draft)
        logger.info("Traffic colors saved: %s", draft)
        if on_change:
            on_change()
        win.destroy()

    tk.Button(btn_row, text="恢复默认", command=on_reset, width=10).pack(side="left")
    tk.Button(btn_row, text="保存", command=on_save, width=10).pack(side="right")

    def on_close() -> None:
        global _window
        _window = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)
