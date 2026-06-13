"""AI engine registration — import-safe without numpy/torch."""

from __future__ import annotations

from typing import Any

_active_engine: Any | None = None


def set_active_engine(engine: Any | None) -> None:
    global _active_engine
    _active_engine = engine


def get_active_engine() -> Any | None:
    return _active_engine


def invalidate_config_cache() -> None:
    engine = _active_engine
    if engine is not None:
        engine.invalidate_config_cache()
