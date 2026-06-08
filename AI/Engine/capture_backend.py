"""Unified capture: NDI (dual-PC) or MSS (local screen)."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass

import numpy as np

from AI.Engine.capture import DetectionRegion, ScreenCapture
from AI.Engine.capture_ndi import NDICapture

logger = logging.getLogger('AimSync.AI.CaptureBackend')


@dataclass(frozen=True)
class FrameContext:
    bgr: np.ndarray
    region: DetectionRegion
    image_size: int
    crosshair_x: int
    crosshair_y: int


class CaptureBackend:
    def __init__(self) -> None:
        self._mss = ScreenCapture()
        self._ndi = NDICapture()
        self._mode = 'mss'
        self._ndi_source = ''
        self._main_pc_width = 1920
        self._main_pc_height = 1080
        self._ndi_sources_cache: list[str] = []
        self._ndi_sources_cache_at = 0.0

    @property
    def screen_width(self) -> int:
        if self._mode == 'ndi' and self._ndi.connected:
            return self._ndi.frame_width
        return self._mss.screen_width

    @property
    def screen_height(self) -> int:
        if self._mode == 'ndi' and self._ndi.connected:
            return self._ndi.frame_height
        return self._mss.screen_height

    def configure(
        self,
        *,
        mode: str,
        ndi_source: str = '',
        main_pc_width: int = 1920,
        main_pc_height: int = 1080,
    ) -> None:
        mode = (mode or 'mss').strip().lower()
        self._main_pc_width = max(640, int(main_pc_width or 1920))
        self._main_pc_height = max(480, int(main_pc_height or 1080))
        if mode == 'ndi':
            self._mode = 'ndi'
            self._ndi_source = (ndi_source or '').strip()
            # NDI open/connect runs only on AiEngine thread (cyndilib is not main-thread safe).
        else:
            self._mode = 'mss'

    def list_ndi_sources(self, *, force_refresh: bool = False, cache_ttl_s: float = 8.0) -> list[str]:
        if threading.current_thread().name != 'AiEngine':
            return list(self._ndi_sources_cache)
        now = time.time()
        if (
            not force_refresh
            and self._ndi_sources_cache
            and (now - self._ndi_sources_cache_at) < cache_ttl_s
        ):
            return list(self._ndi_sources_cache)
        if not self._ndi.ensure_finder():
            return list(self._ndi_sources_cache)
        sources = self._ndi.refresh_sources()
        self._ndi_sources_cache = list(sources)
        self._ndi_sources_cache_at = now
        return sources

    def grab_frame(self, image_size: int, use_mouse: bool) -> FrameContext | None:
        if self._mode == 'ndi':
            return self._grab_ndi(image_size)
        return self._grab_mss(image_size, use_mouse)

    def _grab_ndi(self, image_size: int) -> FrameContext | None:
        if not self._ndi.ensure_finder():
            return None
        if self._ndi_source and not self._ndi.connected:
            self._ndi.select_source(self._ndi_source)
        bgr = self._ndi.grab_bgr()
        if bgr is None:
            return None
        h, w = bgr.shape[:2]
        side = min(w, h, image_size)
        left = (w - side) // 2
        top = (h - side) // 2
        crop = bgr[top : top + side, left : left + side]
        if crop.shape[0] != image_size or crop.shape[1] != image_size:
            if cv2 := _cv2():
                crop = cv2.resize(crop, (image_size, image_size))
        region = DetectionRegion(left=left, top=top, width=side, height=side)
        cx, cy = self._ndi_crosshair(w, h)
        return FrameContext(
            bgr=crop,
            region=region,
            image_size=image_size,
            crosshair_x=cx,
            crosshair_y=cy,
        )

    def _grab_mss(self, image_size: int, use_mouse: bool) -> FrameContext | None:
        region = self._mss.detection_region(image_size, use_mouse)
        rgb = self._mss.grab_rgb(region, image_size)
        if rgb is None:
            return None
        bgr = rgb[:, :, ::-1].copy()
        cx = region.left + region.width // 2
        cy = region.top + region.height // 2
        return FrameContext(
            bgr=bgr,
            region=region,
            image_size=image_size,
            crosshair_x=cx,
            crosshair_y=cy,
        )

    def _ndi_crosshair(self, frame_w: int, frame_h: int) -> tuple[int, int]:
        """Gaming PC crosshair (center of main monitor when stream matches)."""
        if abs(frame_w - self._main_pc_width) <= 2 and abs(frame_h - self._main_pc_height) <= 2:
            return self._main_pc_width // 2, self._main_pc_height // 2
        return frame_w // 2, frame_h // 2

    def stop(self) -> None:
        self._ndi.stop()


def _cv2():
    try:
        import cv2

        return cv2
    except ImportError:
        return None
