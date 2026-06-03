"""Screen capture for AI detection region."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass

import numpy as np

try:
    import mss
except ImportError:  # pragma: no cover
    mss = None


@dataclass(frozen=True)
class DetectionRegion:
    left: int
    top: int
    width: int
    height: int


class ScreenCapture:
    def __init__(self) -> None:
        self._user32 = ctypes.windll.user32
        self._sct = mss.mss() if mss is not None else None

    @property
    def screen_width(self) -> int:
        return int(self._user32.GetSystemMetrics(0))

    @property
    def screen_height(self) -> int:
        return int(self._user32.GetSystemMetrics(1))

    def cursor_position(self) -> tuple[int, int]:
        class POINT(ctypes.Structure):
            _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long)]

        point = POINT()
        self._user32.GetCursorPos(ctypes.byref(point))
        return int(point.x), int(point.y)

    def detection_region(self, image_size: int, use_mouse: bool) -> DetectionRegion:
        if use_mouse:
            cx, cy = self.cursor_position()
        else:
            cx = self.screen_width // 2
            cy = self.screen_height // 2
        half = image_size // 2
        left = max(0, cx - half)
        top = max(0, cy - half)
        width = min(image_size, self.screen_width - left)
        height = min(image_size, self.screen_height - top)
        return DetectionRegion(left, top, width, height)

    def grab_rgb(self, region: DetectionRegion, target_size: int) -> np.ndarray | None:
        if self._sct is None:
            return None
        monitor = {
            'left': region.left,
            'top': region.top,
            'width': region.width,
            'height': region.height,
        }
        shot = self._sct.grab(monitor)
        frame = np.asarray(shot)[:, :, :3]
        if region.width != target_size or region.height != target_size:
            from PIL import Image

            image = Image.fromarray(frame)
            image = image.resize((target_size, target_size), Image.Resampling.BILINEAR)
            frame = np.asarray(image)
        return frame
