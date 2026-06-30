"""Background AI thread."""

from __future__ import annotations

import logging
import threading
import time

from app.ai.engine import AiEngine
from app.ai.lifecycle import set_active_engine
from app.ai.ndi_control import request_ndi_refresh
from app.core.ai_free_quota import get_ai_free_quota_manager
from app.core.config import load_config, save_config

logger = logging.getLogger('KryptAim.rebuild.AiWorker')


def ai_worker(stop_event: threading.Event) -> None:
    engine = AiEngine()
    set_active_engine(engine)
    engine.capture.start_capture_loop()
    engine.start_detection_loop()
    request_ndi_refresh()
    quota = get_ai_free_quota_manager()
    last_quota_tick = 0.0
    try:
        while not stop_event.is_set():
            try:
                config = load_config()
                enabled = bool(config.get('ai_enabled'))
                quota.sync_engine_state(enabled)
                now = time.time()
                if now - last_quota_tick >= 1.0:
                    last_quota_tick = now
                    if enabled and quota.tick():
                        cfg = load_config()
                        if cfg.get('ai_enabled'):
                            cfg['ai_enabled'] = False
                            save_config(cfg)
                            quota.sync_engine_state(False)
                            logger.info('Free Vision AI daily limit reached — engine stopped')
                engine.tick()
            except Exception:
                logger.exception('AI tick failed')
                time.sleep(0.1)
    finally:
        quota.shutdown()
        engine.stop()
        set_active_engine(None)
