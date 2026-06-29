"""Windows floating traffic-light panel (traffic / kun / custom styles)."""

from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from typing import Callable

from ..focus import focus_instance
from ..models import LightState, MonitoredInstance
from ..settings import get_display_mode
from ..styles import asset_path, get_style
from .image_assets import AnimatedGifLabel, assets_dir

logger = logging.getLogger(__name__)

ITEM_W = 96
ITEM_H = 120
ITEM_GAP = 10
PAD_X = 12
PAD_Y = 10
CLOSE_SIZE = 20

DOT_COLORS = {
    LightState.RUNNING: ("#ff2e26", "#8c241f"),
    LightState.WAITING: ("#ffd100", "#8c6f00"),
    LightState.IDLE: ("#26e661", "#1f7a37"),
}

STATE_TIPS = {
    LightState.RUNNING: "🔴 工作中",
    LightState.WAITING: "🟡 待确认",
    LightState.IDLE: "🟢 空闲",
}

KUN_ASSETS = {
    LightState.RUNNING: ("kun.gif", True),
    LightState.WAITING: ("kun_waiting.gif", True),
    LightState.IDLE: ("kun_done.jpg", False),
}


def _short_label(name: str, max_len: int = 16) -> str:
    name = name.strip() or "Untitled"
    return name if len(name) <= max_len else name[: max_len - 1] + "…"


def _label_for_instance(instance: MonitoredInstance) -> str:
    project = instance.extra.get("project") or instance.extra.get("workspace")
    if project:
        return _short_label(str(project))
    if " · " in instance.display_name:
        return _short_label(instance.display_name.split(" · ")[-1])
    return _short_label(instance.display_name)


class _TrafficItem(tk.Frame):
    def __init__(self, master: tk.Misc, on_click: Callable[[MonitoredInstance], None]) -> None:
        super().__init__(master, bg="#212121", width=ITEM_W, height=ITEM_H)
        self._on_click = on_click
        self._instance: MonitoredInstance | None = None
        self._dots: dict[LightState, tk.Canvas] = {}
        housing = tk.Frame(self, bg="#141414", padx=6, pady=8)
        housing.pack()
        for state in (LightState.RUNNING, LightState.WAITING, LightState.IDLE):
            c = tk.Canvas(housing, width=22, height=22, bg="#141414", highlightthickness=0)
            c.pack(side="left", padx=3)
            self._dots[state] = c
        self._name = tk.Label(self, text="", fg="white", bg="#212121", font=("Segoe UI", 9, "bold"))
        self._name.pack(pady=(4, 0))
        self.bind("<Button-1>", self._click)
        self._name.bind("<Button-1>", self._click)
        housing.bind("<Button-1>", self._click)

    def _click(self, _event=None) -> None:
        if self._instance:
            self._on_click(self._instance)

    def update_instance(self, instance: MonitoredInstance) -> None:
        self._instance = instance
        self._name.configure(text=_label_for_instance(instance))
        for state, canvas in self._dots.items():
            on_c, off_c = DOT_COLORS[state]
            color = on_c if instance.state == state else off_c
            canvas.delete("all")
            canvas.create_oval(2, 2, 20, 20, fill=color, outline="")
        tip = f"{instance.display_name}\n{STATE_TIPS.get(instance.state, '')}\n{instance.state_reason}"
        self.configure(cursor="hand2")
        for w in (self, self._name):
            w.bind("<Enter>", lambda _e, t=tip: self._show_tip(t))
        self._show_tip(tip)

    def _show_tip(self, text: str) -> None:
        # Simple tooltip via title on frame
        self._name.configure(text=_label_for_instance(self._instance) if self._instance else "")


class _ImageItem(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        on_click: Callable[[MonitoredInstance], None],
        *,
        mode: str,
        style_id: str | None = None,
    ) -> None:
        super().__init__(master, bg="#212121", width=ITEM_W, height=ITEM_H)
        self._on_click = on_click
        self._mode = mode
        self._style_id = style_id
        self._instance: MonitoredInstance | None = None
        self._gif = AnimatedGifLabel(self, assets_dir() / "kun.gif")
        self._gif.widget.pack()
        self._name = tk.Label(self, text="", fg="white", bg="#212121", font=("Segoe UI", 9, "bold"))
        self._name.pack(pady=(2, 0))
        for w in (self, self._gif.widget, self._name):
            w.bind("<Button-1>", self._click)

    def _click(self, _event=None) -> None:
        if self._instance:
            self._on_click(self._instance)

    def _kun_asset(self, state: LightState) -> tuple[Path, bool]:
        name, animated = KUN_ASSETS[state]
        return assets_dir() / name, animated

    def _custom_asset(self, state: LightState) -> tuple[Path | None, bool]:
        if not self._style_id:
            return None, False
        path = asset_path(self._style_id, state.value)  # type: ignore[arg-type]
        if not path.is_file():
            return None, False
        return path, path.suffix.lower() == ".gif"

    def update_instance(self, instance: MonitoredInstance) -> None:
        self._instance = instance
        self._name.configure(text=_label_for_instance(instance))
        if self._mode == "kun":
            path, animated = self._kun_asset(instance.state)
            if animated:
                self._gif.load_animated(path)
            else:
                self._gif.stop()
                self._gif.set_static(path)
        elif self._mode == "custom" and self._style_id:
            path, animated = self._custom_asset(instance.state)
            if path is None:
                self._gif.widget.configure(text="?", image="")
                return
            if animated:
                self._gif.load_animated(path)
            else:
                self._gif.stop()
                self._gif.set_static(path)

    def destroy(self) -> None:
        self._gif.destroy()
        super().destroy()


class WinTrafficLightPanel:
    """Floating panel matching macOS TrafficLightPanel API."""

    def __init__(self, on_close: Callable[[], None] | None = None) -> None:
        self._on_close = on_close
        self._root = tk.Tk()
        self._root.withdraw()
        self._win = tk.Toplevel(self._root)
        self._win.title("Agent Light")
        self._win.attributes("-topmost", True)
        self._win.configure(bg="#212121")
        self._win.resizable(False, False)
        self._win.protocol("WM_DELETE_WINDOW", self._handle_close)
        self._win.geometry(f"+{self._root.winfo_screenwidth() // 2 - 120}+40")

        header = tk.Frame(self._win, bg="#212121")
        header.pack(fill="x", padx=PAD_X, pady=(PAD_Y, 0))
        close_btn = tk.Button(
            header,
            text="✕",
            command=self._handle_close,
            bg="#333",
            fg="white",
            relief="flat",
            width=2,
        )
        close_btn.pack(side="right")

        self._canvas = tk.Frame(self._win, bg="#212121", padx=PAD_X, pady=PAD_Y)
        self._canvas.pack()
        self._items: dict[str, tk.Frame] = {}
        self._empty = tk.Label(
            self._canvas,
            text="等待 AI 工具…",
            fg="#aaa",
            bg="#212121",
            font=("Segoe UI", 10),
        )
        self._display_mode = get_display_mode()
        self._last_instances: list[MonitoredInstance] = []

    def _handle_close(self) -> None:
        if self._on_close:
            self._on_close()

    def set_display_mode(self, display_mode: str) -> None:
        if self._display_mode == display_mode:
            return
        self._display_mode = display_mode
        for item in list(self._items.values()):
            item.destroy()
        self._items.clear()
        if self._last_instances:
            self.update(self._last_instances)
        self.show()

    def show(self) -> None:
        self._win.deiconify()
        self._win.lift()

    def _make_item(self, inst: MonitoredInstance) -> tk.Frame:
        if self._display_mode == "kun":
            return _ImageItem(self._canvas, focus_instance, mode="kun")
        if self._display_mode.startswith("custom:"):
            style_id = self._display_mode.split(":", 1)[1]
            return _ImageItem(self._canvas, focus_instance, mode="custom", style_id=style_id)
        return _TrafficItem(self._canvas, focus_instance)

    def update(self, instances: list[MonitoredInstance]) -> None:
        self._last_instances = list(instances)
        current = {i.instance_id for i in instances}
        for iid in list(self._items):
            if iid not in current:
                self._items[iid].destroy()
                del self._items[iid]

        for inst in instances:
            if inst.instance_id in self._items:
                item = self._items[inst.instance_id]
                if hasattr(item, "update_instance"):
                    item.update_instance(inst)
            else:
                item = self._make_item(inst)
                item.update_instance(inst)
                item.pack(side="left", padx=ITEM_GAP // 2)
                self._items[inst.instance_id] = item

        if instances:
            self._empty.pack_forget()
        else:
            self._empty.pack(pady=20)

    def poll_events(self) -> None:
        try:
            self._root.update_idletasks()
            self._root.update()
        except tk.TclError:
            pass

    def mainloop_tick(self, callback: Callable[[], None]) -> None:
        callback()
        self._root.after(1500, lambda: self.mainloop_tick(callback))

    @property
    def tk_root(self) -> tk.Tk:
        return self._root
