"""NDI capture for dual-PC (gaming PC stream to AimSync PC)."""

from __future__ import annotations

import logging
import time

import numpy as np

logger = logging.getLogger('AimSync.AI.NDI')

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

_CYNDILIB_IMPORT_ERROR = ''
try:
    from cyndilib.finder import Finder
    from cyndilib.receiver import Receiver
    from cyndilib.video_frame import VideoFrameSync
    from cyndilib.wrapper.ndi_recv import RecvBandwidth, RecvColorFormat
except ImportError as exc:  # pragma: no cover
    _CYNDILIB_IMPORT_ERROR = str(exc)
    Finder = None
    Receiver = None
    VideoFrameSync = None
    RecvColorFormat = None
    RecvBandwidth = None


def _ndi_unavailable_message() -> str:
    import sys

    detail = f' ({_CYNDILIB_IMPORT_ERROR})' if _CYNDILIB_IMPORT_ERROR else ''
    if getattr(sys, 'frozen', False):
        return (
            'NDI (cyndilib) is missing inside this AimSync build'
            f'{detail}. Rebuild with cyndilib installed in the build venv '
            '(scripts\\create_build_venv.bat, build_app.bat), '
            'or run from source Python instead of an old .exe.'
        )
    if 'wrapper.common' in _CYNDILIB_IMPORT_ERROR or 'wrapper' in _CYNDILIB_IMPORT_ERROR:
        return (
            'cyndilib is installed but native modules failed to load'
            f'{detail}. Use the same Python as AimSync: '
            f'"{sys.executable}" -m pip install --force-reinstall --no-cache-dir cyndilib '
            'then scripts\\diagnose_ndi.py. Plain "pip install" often targets a different Python.'
        )
    return (
        'cyndilib not available in this Python'
        f'{detail}. Re-run scripts\\install_aimsync_pc.bat or: '
        f'"{sys.executable}" -m pip install cyndilib'
    )


class NDICapture:
    def __init__(self) -> None:
        self.frame_width = 640
        self.frame_height = 640
        self._finder = None
        self._receiver = None
        self._video_frame = None
        self._available_sources: list[str] = []
        self._desired_source = ''
        self._connected = False
        self._last_error = ''

    @property
    def last_error(self) -> str:
        return self._last_error

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def is_available(self) -> bool:
        return Finder is not None and Receiver is not None

    @property
    def import_error(self) -> str:
        return _CYNDILIB_IMPORT_ERROR

    def ensure_finder(self) -> bool:
        """Open NDI finder/receiver if cyndilib is loaded (idempotent)."""
        if not self.is_available:
            self._last_error = _ndi_unavailable_message()
            return False
        if self._finder is not None and self._receiver is not None:
            return True
        return self.start()

    def start(self) -> bool:
        if not self.is_available:
            self._last_error = _ndi_unavailable_message()
            return False
        try:
            self._finder = Finder()
            self._finder.open()
            self._receiver = Receiver(
                color_format=RecvColorFormat.RGBX_RGBA,
                bandwidth=RecvBandwidth.lowest,
            )
            self._video_frame = VideoFrameSync()
            self._receiver.frame_sync.set_video_frame(self._video_frame)
            self.refresh_sources()
            return True
        except Exception as exc:
            msg = str(exc)
            self._finder = None
            self._receiver = None
            self._video_frame = None
            if 'ndi' in msg.lower() or 'dll' in msg.lower() or 'load' in msg.lower():
                self._last_error = (
                    f'{msg} — Install NDI Runtime on this PC: https://ndi.link/NDIRedistV6'
                )
            else:
                self._last_error = msg
            logger.exception('NDI start failed')
            return False

    def stop(self) -> None:
        try:
            if self._receiver is not None:
                try:
                    self._receiver.set_source(None)
                except Exception:
                    pass
            if self._finder is not None:
                self._finder.close()
        except Exception as exc:
            logger.debug('NDI stop: %s', exc)
        self._finder = None
        self._receiver = None
        self._video_frame = None
        self._connected = False

    def refresh_sources(self) -> list[str]:
        if self._finder is None:
            return []
        try:
            self._available_sources = list(self._finder.get_source_names() or [])
        except Exception:
            self._available_sources = []
        return list(self._available_sources)

    def list_sources(self) -> list[str]:
        return list(self._available_sources)

    def select_source(self, name: str) -> bool:
        self._desired_source = (name or '').strip()
        if not self._desired_source or self._finder is None or self._receiver is None:
            return False
        if self._desired_source not in self._available_sources:
            self.refresh_sources()
        try:
            source = self._finder.get_source(self._desired_source)
            if source is None:
                self._last_error = f"NDI source '{self._desired_source}' not found"
                self._connected = False
                return False
            self._receiver.set_source(source)
            for _ in range(200):
                if self._receiver.is_connected():
                    self._connected = True
                    self._last_error = ''
                    return True
                time.sleep(0.01)
            self._last_error = 'NDI receiver connection timeout'
            self._connected = False
            return False
        except Exception as exc:
            self._last_error = str(exc)
            self._connected = False
            return False

    def grab_bgr(self) -> np.ndarray | None:
        if not self._connected or self._receiver is None or self._video_frame is None:
            return None
        if cv2 is None:
            self._last_error = 'opencv-python required for NDI frames'
            return None
        try:
            if not self._receiver.is_connected():
                self._connected = False
                return None
            # Drain queued NDI frames so inference uses the latest (OBS may send high fps).
            for _ in range(8):
                self._receiver.frame_sync.capture_video()
                if min(self._video_frame.xres, self._video_frame.yres) == 0:
                    return None
            self.frame_width = int(self._video_frame.xres)
            self.frame_height = int(self._video_frame.yres)
            frame = np.frombuffer(self._video_frame, dtype=np.uint8).copy()
            frame = frame.reshape((self.frame_height, self.frame_width, 4))
            return cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        except Exception as exc:
            self._last_error = str(exc)
            return None

    def crosshair_in_frame(self) -> tuple[int, int]:
        return self.frame_width // 2, self.frame_height // 2
