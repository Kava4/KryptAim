"""Thread-safe NDI refresh requests (finder runs on AI worker thread only)."""

from __future__ import annotations

import threading

_refresh_event = threading.Event()
_sources_lock = threading.Lock()
_cached_sources: list[str] = []


def request_ndi_refresh() -> None:
    _refresh_event.set()


def consume_ndi_refresh_request() -> bool:
    if not _refresh_event.is_set():
        return False
    _refresh_event.clear()
    return True


def set_ndi_sources(sources: list[str]) -> None:
    with _sources_lock:
        _cached_sources[:] = list(sources)


def get_ndi_sources() -> list[str]:
    with _sources_lock:
        return list(_cached_sources)
