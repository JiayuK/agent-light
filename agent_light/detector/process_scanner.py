"""Scan running AI tool instances (platform dispatch)."""

from __future__ import annotations

import sys

if sys.platform == "darwin":
    from .process_scanner_darwin import scan_instances
elif sys.platform == "win32":
    from .process_scanner_win32 import scan_instances
else:

    def scan_instances():
        return []


__all__ = ["scan_instances"]
