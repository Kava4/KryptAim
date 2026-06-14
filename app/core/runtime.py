"""Runtime flags."""

from __future__ import annotations

import os
import sys


from app.core.env import env_flag


def dev_mode_enabled(argv: list[str] | None = None) -> bool:
    if env_flag('DEV'):
        return True
    args = argv if argv is not None else sys.argv
    return '--dev' in args
