"""App root / frozen bundle paths."""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, 'frozen', False))


def app_root() -> Path:
    """Directory to chdir into — rebuild root in dev, exe folder when frozen."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def bundle_root() -> Path:
    """PyInstaller _MEIPASS or app root in dev."""
    if is_frozen():
        return Path(getattr(sys, '_MEIPASS', app_root()))
    return app_root()


def web_root() -> Path:
    """Flask static/templates root."""
    bundled = bundle_root() / 'web'
    if (bundled / 'static').is_dir() and (bundled / 'templates').is_dir():
        return bundled
    dev = app_root() / 'web'
    if (dev / 'static').is_dir():
        return dev
    return Path(__file__).resolve().parents[2] / 'web'
