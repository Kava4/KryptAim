"""Runtime flags."""

from __future__ import annotations

import os
import sys


def dev_mode_enabled(argv: list[str] | None = None) -> bool:
    if os.environ.get('AIMSYNC_DEV', '').strip().lower() in {'1', 'true', 'yes'}:
        return True
    args = argv if argv is not None else sys.argv
    return '--dev' in args
