"""Bring monitored AI tool instances to the foreground (platform dispatch)."""

from __future__ import annotations

import sys

from .models import MonitoredInstance

if sys.platform == "darwin":
    from .platform.focus_darwin import focus_instance as _focus_instance
elif sys.platform == "win32":
    from .platform.focus_win32 import focus_instance as _focus_instance
else:

    def _focus_instance(instance: MonitoredInstance) -> None:
        return None


def focus_instance(instance: MonitoredInstance) -> None:
    _focus_instance(instance)


__all__ = ["focus_instance"]
