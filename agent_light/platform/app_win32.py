"""Windows x64 tray application — feature parity with macOS."""

from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox

from ..agent_hooks import format_hook_results, hooks_install_status, hooks_need_install, install_all_hooks_detailed, uninstall_all_hooks
from ..constants import APP_DATA_DIR, APP_LOGGER_NAME
from ..detector import analyze_states, scan_instances
from ..logging_config import LOG_DIR, LOG_FILE, is_quiet_mode
from ..settings import (
    get_display_mode,
    get_hooks_reminder_dismissed,
    set_display_mode,
    set_hooks_reminder_dismissed,
)
from ..shutdown import consume_shutdown_flag, register_shutdown, remove_pid, write_pid
from ..styles import get_style, is_style_complete, list_complete_styles, reload_styles
from ..tool_paths import format_user_path
from ..tool_presence import (
    TOOL_LABELS,
    format_available_tools_summary,
    format_missing_tools_summary,
    get_available_tools,
)
from ..ui_win import WinTrafficLightPanel, show_color_god, show_style_manager
from .main_thread import drain_win_queue

logger = logging.getLogger(APP_LOGGER_NAME)

POLL_INTERVAL_MS = 1500


class WinApp:
    def __init__(self) -> None:
        self._shutdown = False
        self._panel = WinTrafficLightPanel(on_close=lambda: self.shutdown("panel-close"))
        self._tray_icon = None
        self._tray_thread: threading.Thread | None = None

    def shutdown(self, reason: str = "user") -> None:
        if self._shutdown:
            return
        self._shutdown = True
        logger.info("Shutting down (%s)", reason)
        remove_pid()
        if self._tray_icon:
            try:
                self._tray_icon.visible = False
                self._tray_icon.stop()
            except Exception:
                pass
        try:
            self._panel.tk_root.quit()
        except tk.TclError:
            pass

    def _tray_title(self) -> str:
        mode = get_display_mode()
        if mode == "kun":
            return "💗"
        if mode.startswith("custom:"):
            style = get_style(mode.split(":", 1)[1])
            return style.banner_emoji if style else "🎨"
        return "🚦"

    def _hook_install_label(self) -> str:
        available = get_available_tools()
        if not available:
            return "安装 Hook（未检测到工具）"
        status = hooks_install_status()
        installed = sum(1 for tool in available if status.get(tool))
        total = len(available)
        suffix = f" ({installed}/{total})" if installed < total else " ✓"
        return f"安装 Hook{suffix}"

    def _apply_display_mode(self, mode: str) -> None:
        if mode.startswith("custom:"):
            style_id = mode.split(":", 1)[1]
            if not is_style_complete(style_id):
                messagebox.showwarning("风格未完成", "请先在「我爱发明」中填写全部必填项并保存。")
                return
        set_display_mode(mode)
        self._panel.set_display_mode(mode)
        self._rebuild_tray()

    def _on_traffic_colors_changed(self) -> None:
        self._panel.refresh_traffic_colors()

    def _on_styles_changed(self) -> None:
        mode = get_display_mode()
        if mode.startswith("custom:"):
            style_id = mode.split(":", 1)[1]
            if get_style(style_id) is None:
                self._apply_display_mode("traffic")
                return
        reload_styles()
        self._rebuild_tray()
        if self._panel._last_instances:
            self._panel.update(self._panel._last_instances)

    def _install_hooks(self) -> None:
        if not get_available_tools():
            messagebox.showwarning(
                "未检测到 AI 工具",
                "本机未发现 Cursor、Claude Code 或 Codex。\n\n"
                f"可在 {format_user_path(APP_DATA_DIR / 'settings.json')} 配置 tool_paths。",
            )
            return
        results = install_all_hooks_detailed(sys.executable)
        self._rebuild_tray()
        failed = [r for r in results if not r.ok and not r.skipped]
        changed = [r for r in results if r.ok and not r.skipped]
        summary = format_available_tools_summary() + "\n\n" + format_hook_results(results)
        if failed:
            messagebox.showwarning("Hook 安装未全部成功", summary + "\n\n请重启对应 AI 工具后生效。")
        elif changed:
            messagebox.showinfo("Hook 安装完成", summary + "\n\n请重启本次变更涉及的工具后生效。")
            set_hooks_reminder_dismissed(True)
        else:
            messagebox.showinfo("Hook 已是最新", summary + "\n\n已检测到的工具 Hook 均完整。")

    def _uninstall_hooks(self) -> None:
        from ..agent_hooks import get_installed_hook_tools

        installed = get_installed_hook_tools()
        if not installed:
            messagebox.showinfo("没有可删除的 Hook", "当前未发现已安装的 Agent Light Hook。")
            return
        tool_names = "、".join(TOOL_LABELS.get(t, t) for t in installed)
        if not messagebox.askyesno(
            "删除 Agent Light Hook？",
            f"将移除以下工具的 Agent Light Hook：{tool_names}\n\n"
            "只会删除 Agent Light 添加的脚本和配置项。",
        ):
            return
        results = uninstall_all_hooks()
        self._rebuild_tray()
        failed = [r for r in results if not r.ok and not r.skipped]
        if failed:
            messagebox.showwarning("Hook 删除未全部成功", format_hook_results(results))
        else:
            messagebox.showinfo("Hook 已删除", format_hook_results(results) + "\n\n请重启对应 AI 工具后生效。")

    def _show_about(self) -> None:
        log_line = "静默模式（无日志）" if is_quiet_mode() else f"日志：{format_user_path(LOG_FILE)}"
        messagebox.showinfo(
            "Agent Light",
            "AI 工具交通信号灯监控\n\n"
            "🔴 运行中  🟡 人工确认  🟢 结束\n\n"
            "托盘菜单可切换交通灯 / 坤坤 / 自定义风格\n"
            "「我爱发明」管理自定义图片与动图\n\n"
            f"{log_line}",
        )

    def _open_logs(self) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(str(LOG_DIR))  # type: ignore[attr-defined]

    def _maybe_show_hooks_reminder(self) -> None:
        if get_hooks_reminder_dismissed() or not hooks_need_install():
            return
        available = get_available_tools()
        if not available:
            return
        missing = format_missing_tools_summary()
        choice = messagebox.askyesnocancel(
            "尚未安装 Agent Hook",
            f"{format_available_tools_summary()}\n{missing}\n\n"
            "未安装 Hook 时无法检测已安装工具的运行状态。\n"
            "安装时会自动检测配置目录，并合并写入，不会覆盖你已有的 Hook 配置。\n\n"
            "选择「是」立即安装，「否」稍后提醒，「取消」不再提醒。",
        )
        if choice is True:
            self._install_hooks()
        elif choice is False:
            return
        else:
            set_hooks_reminder_dismissed(True)

    def _build_menu(self):
        import pystray
        from PIL import Image, ImageDraw

        menu_items = [
            pystray.MenuItem("显示面板", lambda: self._panel.show()),
            pystray.MenuItem("🚦 交通灯", lambda: self._apply_display_mode("traffic")),
            pystray.MenuItem("我爱坤坤💗💗", lambda: self._apply_display_mode("kun")),
        ]
        reload_styles()
        styles = list_complete_styles()
        if styles:
            menu_items.append(pystray.Menu.SEPARATOR)
            for style in styles:
                menu_items.append(
                    pystray.MenuItem(
                        f"{style.banner_emoji} {style.name}",
                        lambda s=style: self._apply_display_mode(f"custom:{s.id}"),
                    )
                )
        menu_items.extend(
            [
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("我爱发明", lambda: show_style_manager(on_change=self._on_styles_changed, master=self._panel.tk_root)),
                pystray.MenuItem("颜色の神", lambda: show_color_god(on_change=self._on_traffic_colors_changed, master=self._panel.tk_root)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(self._hook_install_label, lambda: self._install_hooks()),
                pystray.MenuItem("删除 Hook", lambda: self._uninstall_hooks()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("关于", self._show_about),
            ]
        )
        if not is_quiet_mode():
            menu_items.append(pystray.MenuItem("打开日志", self._open_logs))
        menu_items.extend(
            [
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出 Agent Light", lambda: self.shutdown("tray-quit")),
            ]
        )
        img = Image.new("RGB", (64, 64), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        draw.ellipse((8, 8, 56, 56), fill=(46, 204, 113))
        return pystray.Icon("agent-light", img, "Agent Light", pystray.Menu(*menu_items))

    def _rebuild_tray(self) -> None:
        if not self._tray_icon:
            return
        # pystray: update menu by replacing icon
        old = self._tray_icon
        self._tray_icon = self._build_menu()
        try:
            old.visible = False
            old.stop()
        except Exception:
            pass
        self._tray_thread = threading.Thread(target=self._tray_icon.run, daemon=True)
        self._tray_thread.start()

    def _start_tray(self) -> None:
        self._tray_icon = self._build_menu()
        self._tray_thread = threading.Thread(target=self._tray_icon.run, daemon=True)
        self._tray_thread.start()

    def _tick(self) -> None:
        if self._shutdown:
            return
        drain_win_queue()
        if consume_shutdown_flag():
            self.shutdown("stop-flag")
            return
        try:
            instances = scan_instances()
            instances = analyze_states(instances)
            self._panel.update(instances)
        except Exception:
            logger.exception("Poll tick failed")
        self._panel.tk_root.after(POLL_INTERVAL_MS, self._tick)

    def run(self) -> None:
        write_pid()
        register_shutdown(self.shutdown)
        self._start_tray()
        self._panel.show()
        self._panel.tk_root.after(300, self._maybe_show_hooks_reminder)
        self._panel.tk_root.after(POLL_INTERVAL_MS, self._tick)
        logger.info("Agent Light started (Windows x64)")
        self._panel.tk_root.mainloop()


def run_app(_args: argparse.Namespace) -> None:
    WinApp().run()


__all__ = ["run_app"]
