"""Shared AI runtime status for GUI polling."""

from __future__ import annotations

import threading
from dataclasses import dataclass


@dataclass
class AiRuntimeStatus:
    state: str = 'off'
    detail: str = ''
    trigger_armed: bool = False
    last_block_reason: str = ''
    aim_block_reason: str = ''
    in_zone_count: int = 0
    ndi_connected: bool = False
    ndi_has_video: bool = False
    ndi_source: str = ''
    frame_width: int = 0
    frame_height: int = 0
    capture_fps: float = 0.0
    model_loaded: bool = False
    model_name: str = ''
    detection_count: int = 0
    inference_ms: float = 0.0


_lock = threading.Lock()
_runtime = AiRuntimeStatus()


def get_ai_runtime_status() -> AiRuntimeStatus:
    with _lock:
        return AiRuntimeStatus(
            state=_runtime.state,
            detail=_runtime.detail,
            trigger_armed=_runtime.trigger_armed,
            last_block_reason=_runtime.last_block_reason,
            aim_block_reason=_runtime.aim_block_reason,
            in_zone_count=_runtime.in_zone_count,
            ndi_connected=_runtime.ndi_connected,
            ndi_has_video=_runtime.ndi_has_video,
            ndi_source=_runtime.ndi_source,
            frame_width=_runtime.frame_width,
            frame_height=_runtime.frame_height,
            capture_fps=_runtime.capture_fps,
            model_loaded=_runtime.model_loaded,
            model_name=_runtime.model_name,
            detection_count=_runtime.detection_count,
            inference_ms=_runtime.inference_ms,
        )


def update_ai_runtime_status(**kwargs) -> None:
    with _lock:
        for key, value in kwargs.items():
            if hasattr(_runtime, key):
                setattr(_runtime, key, value)
