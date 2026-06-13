"""Background AI thread."""

from __future__ import annotations

import logging
import threading
import time

from app.ai.engine import AiEngine
from app.ai.lifecycle import set_active_engine
from app.ai.ndi_control import request_ndi_refresh

logger = logging.getLogger('AimSync.rebuild.AiWorker')


def ai_worker(stop_event: threading.Event) -> None:
    engine = AiEngine()
    set_active_engine(engine)
    engine.capture.start_capture_loop()
    engine.start_detection_loop()
    request_ndi_refresh()
    try:
        while not stop_event.is_set():
            try:
                engine.tick()
            except Exception:
                logger.exception('AI tick failed')
                time.sleep(0.1)
    finally:
        engine.stop()
        set_active_engine(None)
