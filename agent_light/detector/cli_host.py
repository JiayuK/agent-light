"""Resolve the host app for a CLI session (standalone terminal or IDE-embedded terminal)."""

from __future__ import annotations

import sys
from dataclasses import dataclass

import psutil

SHELL_NAMES = {"zsh", "bash", "fish", "sh", "login", "cmd.exe", "powershell.exe", "pwsh.exe"}

TERMINAL_NAMES = {
    "iterm2",
    "iterm",
    "terminal",
    "warp",
    "alacritty",
    "kitty",
    "windowsterminal.exe",
    "wt.exe",
}

IDE_PROCESS_ALIASES: dict[str, str] = {
    "idea": "IntelliJ IDEA",
    "idea64.exe": "IntelliJ IDEA",
    "pycharm": "PyCharm",
    "pycharm64.exe": "PyCharm",
    "webstorm": "WebStorm",
    "webstorm64.exe": "WebStorm",
    "goland": "GoLand",
    "goland64.exe": "GoLand",
    "clion": "CLion",
    "clion64.exe": "CLion",
    "rider": "Rider",
    "rider64.exe": "Rider",
    "phpstorm": "PhpStorm",
    "phpstorm64.exe": "PhpStorm",
    "datagrip": "DataGrip",
    "datagrip64.exe": "DataGrip",
    "rubymine": "RubyMine",
    "rubymine64.exe": "RubyMine",
    "studio": "Android Studio",
    "studio64.exe": "Android Studio",
    "code": "Visual Studio Code",
    "code.exe": "Visual Studio Code",
    "code - insiders": "Visual Studio Code - Insiders",
    "code - insiders.exe": "Visual Studio Code - Insiders",
}

STANDALONE_TERMINAL_APP_NAMES = frozenset(
    {"Terminal", "iTerm", "Warp", "Alacritty", "Kitty", "Windows Terminal"}
)

JETBRAINS_MARKERS = ("jetbrains", "android studio", "android-studio")
VSCODE_MARKERS = ("visual studio code", "vscode", "microsoft vs code")


@dataclass(frozen=True)
class CliHostInfo:
    shell_pid: int | None
    host_pid: int | None
    host_app_name: str
    host_kind: str  # "terminal" | "ide"


def _safe_exe(proc: psutil.Process) -> str:
    try:
        return proc.exe() or ""
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return ""


def _macos_app_name_from_exe(exe: str) -> str | None:
    if ".app/" not in exe:
        return None
    for part in exe.split("/"):
        if part.endswith(".app"):
            return part[:-4]
    return None


def _windows_product_from_exe(exe: str) -> str | None:
    lower = exe.replace("\\", "/").lower()
    if any(marker in lower for marker in JETBRAINS_MARKERS):
        parts = lower.split("/")
        for idx, part in enumerate(parts):
            if part == "jetbrains" and idx + 1 < len(parts):
                return parts[idx + 1].replace(".exe", "").strip() or None
            if "android studio" in part:
                return "Android Studio"
    if any(marker in lower for marker in VSCODE_MARKERS):
        return "Visual Studio Code"
    return None


def _app_name_from_exe(exe: str) -> str | None:
    if not exe:
        return None
    if sys.platform == "darwin":
        return _macos_app_name_from_exe(exe)
    product = _windows_product_from_exe(exe)
    if product:
        # Normalize JetBrains folder names to friendly labels.
        key = product.lower().replace(" ", "").replace("-", "")
        for alias, label in IDE_PROCESS_ALIASES.items():
            alias_key = alias.replace(".exe", "").replace("-", "")
            if key == alias_key or key.startswith(alias_key):
                return label
        return product
    return None


def _terminal_app_name(proc_name: str) -> str:
    if "iterm" in proc_name:
        return "iTerm"
    if proc_name in {"windowsterminal.exe", "wt.exe"}:
        return "Windows Terminal"
    return proc_name.capitalize() if proc_name else "Terminal"


def _is_ide_app(app_name: str, exe: str, proc_name: str) -> bool:
    if app_name in STANDALONE_TERMINAL_APP_NAMES:
        return False
    lower_exe = exe.lower()
    if proc_name in IDE_PROCESS_ALIASES:
        return True
    if any(marker in lower_exe for marker in JETBRAINS_MARKERS):
        return True
    if any(marker in lower_exe for marker in VSCODE_MARKERS):
        return True
    if app_name in set(IDE_PROCESS_ALIASES.values()):
        return True
    if proc_name == "studio" and "android" in lower_exe:
        return True
    return False


def _walk_ancestors(pid: int) -> list[tuple[int, str, str]]:
    chain: list[tuple[int, str, str]] = []
    try:
        cur = psutil.Process(pid)
        for _ in range(24):
            chain.append((cur.pid, cur.name().lower(), _safe_exe(cur)))
            if cur.ppid() in (0, cur.pid):
                break
            cur = psutil.Process(cur.ppid())
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return chain


def resolve_cli_host(pid: int) -> CliHostInfo:
    shell_pid: int | None = None
    terminal_host: tuple[int, str] | None = None
    ide_host: tuple[int, str] | None = None

    for proc_pid, name, exe in _walk_ancestors(pid):
        if name in SHELL_NAMES and shell_pid is None:
            shell_pid = proc_pid

        if name in TERMINAL_NAMES:
            terminal_host = (proc_pid, _terminal_app_name(name))

        app_name = _app_name_from_exe(exe)
        if app_name and _is_ide_app(app_name, exe, name):
            ide_host = (proc_pid, app_name)
        elif name in IDE_PROCESS_ALIASES:
            ide_host = (proc_pid, IDE_PROCESS_ALIASES[name])

    if terminal_host:
        host_pid, host_app = terminal_host
        return CliHostInfo(shell_pid, host_pid, host_app, "terminal")

    if ide_host:
        host_pid, host_app = ide_host
        return CliHostInfo(shell_pid, host_pid, host_app, "ide")

    return CliHostInfo(shell_pid, None, "Terminal", "terminal")
