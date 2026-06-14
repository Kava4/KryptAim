"""Shared AppData paths for runtime bootstrap."""

from __future__ import annotations

import os
from pathlib import Path


def runtime_dir() -> Path:
    base = Path(os.environ.get('APPDATA') or Path.home()) / 'KryptAim' / 'runtime'
    base.mkdir(parents=True, exist_ok=True)
    return base
