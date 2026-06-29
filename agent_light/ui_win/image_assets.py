"""PIL / Tk image helpers for Windows UI."""

from __future__ import annotations

import logging
from pathlib import Path

import tkinter as tk
from PIL import Image, ImageSequence, ImageTk

logger = logging.getLogger(__name__)

DISPLAY_SIZE = (80, 88)


def assets_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "assets"


def load_static_image(path: Path, size: tuple[int, int] = DISPLAY_SIZE) -> ImageTk.PhotoImage:
    with Image.open(path) as img:
        img = img.convert("RGBA")
        img.thumbnail(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)


class AnimatedGifLabel:
    """Cycle GIF frames on a Tk label."""

    def __init__(self, master: tk.Misc, path: Path, size: tuple[int, int] = DISPLAY_SIZE) -> None:
        self._label = tk.Label(master, bg="#212121", borderwidth=0)
        self._frames: list[ImageTk.PhotoImage] = []
        self._durations: list[int] = []
        self._index = 0
        self._job: str | None = None
        self._running = False
        self._load(path, size)

    @property
    def widget(self) -> tk.Label:
        return self._label

    def _load(self, path: Path, size: tuple[int, int]) -> None:
        self._frames.clear()
        self._durations.clear()
        try:
            with Image.open(path) as img:
                for frame in ImageSequence.Iterator(img):
                    rgba = frame.convert("RGBA")
                    rgba.thumbnail(size, Image.Resampling.LANCZOS)
                    self._frames.append(ImageTk.PhotoImage(rgba))
                    self._durations.append(int(frame.info.get("duration", img.info.get("duration", 80))))
        except OSError as exc:
            logger.warning("Failed to load GIF %s: %s", path, exc)
        if self._frames:
            self._label.configure(image=self._frames[0])

    def start(self) -> None:
        if not self._frames or self._running:
            return
        self._running = True
        self._tick()

    def stop(self) -> None:
        self._running = False
        if self._job and self._label.winfo_exists():
            self._label.after_cancel(self._job)
            self._job = None

    def _tick(self) -> None:
        if not self._running or not self._frames:
            return
        self._index = (self._index + 1) % len(self._frames)
        self._label.configure(image=self._frames[self._index])
        delay = max(self._durations[self._index] if self._durations else 80, 20)
        self._job = self._label.after(delay, self._tick)

    def load_animated(self, path: Path, size: tuple[int, int] = DISPLAY_SIZE) -> None:
        self.stop()
        self._load(path, size)
        if self._frames:
            self.start()

    def set_static(self, path: Path, size: tuple[int, int] = DISPLAY_SIZE) -> None:
        self.stop()
        try:
            photo = load_static_image(path, size)
        except OSError:
            self._label.configure(image="", text="?")
            return
        self._frames = [photo]
        self._label.configure(image=photo)

    def destroy(self) -> None:
        self.stop()
        self._label.destroy()
