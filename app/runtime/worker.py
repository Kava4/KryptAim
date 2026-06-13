"""Background recoil thread."""

from __future__ import annotations

import threading

from app.recoil.engine import run_recoil


def recoil_worker(stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        run_recoil()
