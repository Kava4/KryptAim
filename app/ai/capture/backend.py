"""NDI capture backend — Eventuri-style producer thread + center crop."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass

import numpy as np

from app.ai.capture.ndi import NDICapture
from app.ai.capture.region import DetectionRegion

logger = logging.getLogger('AimSync.rebuild.Capture')


@dataclass(frozen=True)
class FrameContext:
    bgr: np.ndarray
    region: DetectionRegion
    image_size: int
    crosshair_x: int
    crosshair_y: int


def _cv2():
    try:
        import cv2

        return cv2
    except ImportError:
        return None


def center_square_crop(
    bgr_full: np.ndarray,
    *,
    main_pc_width: int,
    main_pc_height: int,
    image_size: int,
) -> FrameContext | None:
    if bgr_full is None or bgr_full.size == 0:
        return None
    h, w = bgr_full.shape[:2]
    side = min(w, h)
    crop_left = (w - side) // 2
    crop_top = (h - side) // 2
    crop = bgr_full[crop_top : crop_top + side, crop_left : crop_left + side]
    bgr = crop
    if crop.shape[0] != image_size or crop.shape[1] != image_size:
        cv2 = _cv2()
        if cv2 is None:
            return None
        bgr = cv2.resize(crop, (image_size, image_size))

    ndi_left = (main_pc_width - w) // 2
    ndi_top = (main_pc_height - h) // 2
    region = DetectionRegion(
        left=ndi_left + crop_left,
        top=ndi_top + crop_top,
        width=side,
        height=side,
    )
    return FrameContext(
        bgr=bgr,
        region=region,
        image_size=image_size,
        crosshair_x=main_pc_width // 2,
        crosshair_y=main_pc_height // 2,
    )


class CaptureBackend:
    """Producer thread polls NDI like eventuri/src/main.py capture_loop."""

    def __init__(self) -> None:
        self._ndi = NDICapture()
        self._ndi_source = ''
        self._main_pc_width = 1920
        self._main_pc_height = 1080
        self._latest_bgr: np.ndarray | None = None
        self._frame_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_selected = ''

    @property
    def ndi(self) -> NDICapture:
        return self._ndi

    def start_capture_loop(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._capture_loop,
            name='NDICapture',
            daemon=True,
        )
        self._thread.start()

    def configure(
        self,
        *,
        ndi_source: str,
        main_pc_width: int = 1920,
        main_pc_height: int = 1080,
    ) -> None:
        self._ndi_source = (ndi_source or '').strip()
        self._main_pc_width = max(640, int(main_pc_width or 1920))
        self._main_pc_height = max(480, int(main_pc_height or 1080))

    def refresh_ndi_sources(self, *, wait_s: float = 0.0) -> list[str]:
        if not self._ndi.ensure_finder():
            return []
        return self._ndi.refresh_sources(wait_s=wait_s)

    def grab_frame(self, image_size: int) -> FrameContext | None:
        self.start_capture_loop()
        with self._frame_lock:
            bgr = self._latest_bgr
        if bgr is None:
            return None
        return center_square_crop(
            bgr,
            main_pc_width=self._main_pc_width,
            main_pc_height=self._main_pc_height,
            image_size=image_size,
        )

    def _capture_loop(self) -> None:
        while not self._stop.is_set():
            try:
                if not self._ndi.ensure_finder():
                    time.sleep(0.2)
                    continue

                try:
                    sources = self._ndi.refresh_sources()
                except Exception:
                    sources = self._ndi.list_sources()

                desired = self._ndi_source
                if desired and desired in sources:
                    if desired != self._last_selected or not self._ndi.connected:
                        self._ndi.select_source(desired)
                        self._last_selected = desired

                bgr = self._ndi.grab_bgr()
                if bgr is not None:
                    with self._frame_lock:
                        self._latest_bgr = bgr
            except Exception as exc:
                logger.debug('NDI capture loop: %s', exc)
                time.sleep(0.01)

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._ndi.stop()
