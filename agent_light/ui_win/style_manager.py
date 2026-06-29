"""Windows style manager window."""

from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable

from ..styles import (
    STATE_KEYS,
    STATE_LABELS,
    CustomStyle,
    create_style,
    delete_style,
    import_state_asset,
    list_styles,
    reload_styles,
    save_style_complete,
    validate_style_draft,
)

logger = logging.getLogger(__name__)

_window: tk.Toplevel | None = None


def show_style_manager(on_change: Callable[[], None] | None = None, master: tk.Misc | None = None) -> None:
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
    win.title("我爱发明 — 自定义风格")
    win.geometry("560x520")
    win.configure(bg="#f5f5f5")
    _window = win

    selected: dict[str, CustomStyle | None] = {"style": None}
    name_var = tk.StringVar()
    emoji_var = tk.StringVar(value="🎨")

    listbox = tk.Listbox(win, height=12, font=("Segoe UI", 11))
    listbox.pack(fill="both", expand=False, padx=12, pady=(12, 6))

    form = tk.Frame(win, bg="#f5f5f5")
    form.pack(fill="x", padx=12, pady=6)
    tk.Label(form, text="名称", bg="#f5f5f5").grid(row=0, column=0, sticky="w")
    tk.Entry(form, textvariable=name_var, width=30).grid(row=0, column=1, sticky="w", pady=2)
    tk.Label(form, text="Banner emoji", bg="#f5f5f5").grid(row=1, column=0, sticky="w")
    tk.Entry(form, textvariable=emoji_var, width=10).grid(row=1, column=1, sticky="w", pady=2)

    asset_frame = tk.LabelFrame(win, text="状态素材（必填）", bg="#f5f5f5")
    asset_frame.pack(fill="x", padx=12, pady=6)
    asset_labels: dict[str, tk.Label] = {}

    def refresh_list() -> None:
        reload_styles()
        listbox.delete(0, tk.END)
        for style in list_styles():
            listbox.insert(tk.END, f"{style.banner_emoji}  {style.name}")

    def on_select(_event=None) -> None:
        idx = listbox.curselection()
        if not idx:
            selected["style"] = None
            return
        styles = list_styles()
        row = int(idx[0])
        if row >= len(styles):
            return
        style = styles[row]
        selected["style"] = style
        name_var.set(style.name)
        emoji_var.set(style.banner_emoji)
        for state in STATE_KEYS:
            from ..styles import asset_path

            path = asset_path(style.id, state)
            asset_labels[state].configure(
                text=path.name if path.is_file() else "未上传",
                fg="green" if path.is_file() else "gray",
            )

    def do_new() -> None:
        try:
            style = create_style("新风格", "🎨")
            refresh_list()
            for i, s in enumerate(list_styles()):
                if s.id == style.id:
                    listbox.selection_clear(0, tk.END)
                    listbox.selection_set(i)
                    on_select()
                    break
        except ValueError as exc:
            messagebox.showerror("错误", str(exc), parent=win)

    def do_save() -> None:
        style = selected["style"]
        if not style:
            messagebox.showwarning("提示", "请先选择或新建风格", parent=win)
            return
        try:
            save_style_complete(style.id, name=name_var.get(), banner_emoji=emoji_var.get())
            refresh_list()
            if on_change:
                on_change()
            messagebox.showinfo("已保存", "风格已保存", parent=win)
        except ValueError as exc:
            messagebox.showerror("无法保存", str(exc), parent=win)

    def do_delete() -> None:
        style = selected["style"]
        if not style:
            return
        if not messagebox.askyesno("删除", f"删除风格「{style.name}」？", parent=win):
            return
        delete_style(style.id)
        selected["style"] = None
        refresh_list()
        if on_change:
            on_change()

    def pick_asset(state: str) -> None:
        style = selected["style"]
        if not style:
            messagebox.showwarning("提示", "请先选择风格", parent=win)
            return
        path = filedialog.askopenfilename(
            parent=win,
            title=f"选择 {STATE_LABELS[state]} 素材",
            filetypes=[
                ("Images", "*.gif *.png *.jpg *.jpeg *.webp"),
                ("All", "*.*"),
            ],
        )
        if not path:
            return
        try:
            import_state_asset(style.id, state, Path(path))  # type: ignore[arg-type]
            on_select()
            if on_change:
                on_change()
        except ValueError as exc:
            messagebox.showerror("导入失败", str(exc), parent=win)

    for state in STATE_KEYS:
        row = tk.Frame(asset_frame, bg="#f5f5f5")
        row.pack(fill="x", pady=2)
        tk.Label(row, text=STATE_LABELS[state], width=10, anchor="w", bg="#f5f5f5").pack(side="left")
        lbl = tk.Label(row, text="未上传", anchor="w", bg="#f5f5f5", fg="gray")
        lbl.pack(side="left", padx=6)
        asset_labels[state] = lbl
        tk.Button(row, text="选择文件…", command=lambda s=state: pick_asset(s)).pack(side="right")

    btns = tk.Frame(win, bg="#f5f5f5")
    btns.pack(fill="x", padx=12, pady=12)
    tk.Button(btns, text="新建", command=do_new).pack(side="left", padx=4)
    tk.Button(btns, text="保存", command=do_save).pack(side="left", padx=4)
    tk.Button(btns, text="删除", command=do_delete).pack(side="left", padx=4)

    listbox.bind("<<ListboxSelect>>", on_select)
    refresh_list()

    def on_close() -> None:
        global _window
        _window = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)
