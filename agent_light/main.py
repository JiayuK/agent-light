"""Agent Light - main entry point."""

from __future__ import annotations

import argparse
import logging
import sys

from .constants import APP_DATA_DIR, APP_LOGGER_NAME
from .logging_config import setup_logging
from .shutdown import install_signal_handlers
from .tool_paths import format_user_path, get_resolved_tool_paths

logger = logging.getLogger(APP_LOGGER_NAME)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agent Light — AI 工具交通信号灯监控")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help=f"启用日志：写入 {APP_DATA_DIR / 'logs'} 并输出到控制台",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def _log_resolved_paths() -> None:
    paths = get_resolved_tool_paths()
    logger.info("Tool paths resolved:")
    for key, value in paths.items():
        logger.info("  %s → %s", key, format_user_path(value))


def main() -> None:
    args = parse_args()
    quiet = not args.verbose if not args.quiet else True
    setup_logging(quiet=quiet)
    install_signal_handlers()
    if not quiet:
        _log_resolved_paths()

    if sys.platform == "win32":
        from .platform.app_win32 import run_app

        run_app(args)
        return

    if sys.platform != "darwin":
        raise SystemExit(f"Unsupported platform: {sys.platform}")

    from .platform.app_darwin import run_app

    run_app(args)


if __name__ == "__main__":
    main()
