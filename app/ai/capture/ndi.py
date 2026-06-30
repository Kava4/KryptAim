"""NDI capture for dual-PC (gaming PC → AimSync PC).

Ported from original_source/eventuri/src/capture.py (NDICamera).
"""

from __future__ import annotations

import logging
import time

import numpy as np

logger = logging.getLogger('AimSync.rebuild.NDI')

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

_CYNDILIB_IMPORT_ERROR = ''
try:
    from cyndilib.audio_frame import AudioFrameSync
    from cyndilib.finder import Finder
    from cyndilib.receiver import Receiver
    from cyndilib.video_frame import VideoFrameSync
    from cyndilib.wrapper.ndi_recv import RecvBandwidth, RecvColorFormat
except ImportError as exc:  # pragma: no cover
    _CYNDILIB_IMPORT_ERROR = str(exc)
    AudioFrameSync = None
    Finder = None
    Receiver = None
    VideoFrameSync = None
    RecvColorFormat = None
    RecvBandwidth = None


def ndi_unavailable_message() -> str:
    detail = f' ({_CYNDILIB_IMPORT_ERROR})' if _CYNDILIB_IMPORT_ERROR else ''
    if 'wrapper' in _CYNDILIB_IMPORT_ERROR:
        return (
            'cyndilib native modules failed to load'
            f'{detail}. pip install --force-reinstall cyndilib, then scripts\\diagnose_ndi.py'
        )
    return f'cyndilib not installed{detail}. pip install cyndilib + NDI Runtime on this PC'


class NDICapture:
    def __init__(self) -> None:
        self.frame_width = 0
        self.frame_height = 0
        self._finder = None
        self._receiver = None
        self._video_frame = None
        self._audio_frame = None
        self._available_sources: list[str] = []
        self._desired_source = ''
        self._connected = False
        self._has_video = False
        self._last_error = ''
        self._pending_connect = False
        self._last_connect_try = 0.0
        self._retry_interval = 0.5

    @property
    def last_error(self) -> str:
        return self._last_error

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def has_video(self) -> bool:
        return self._has_video

    @property
    def selected_source(self) -> str:
        return self._desired_source

    @property
    def is_available(self) -> bool:
        return Finder is not None and Receiver is not None

    def ensure_finder(self) -> bool:
        if not self.is_available:
            self._last_error = ndi_unavailable_message()
            return False
        if self._finder is not None and self._receiver is not None:
            return True
        return self.start()

    def start(self) -> bool:
        if not self.is_available:
            self._last_error = ndi_unavailable_message()
            return False
        try:
            self._finder = Finder()
            self._finder.set_change_callback(self._on_finder_change)
            self._finder.open()
            self._receiver = Receiver(
                color_format=RecvColorFormat.RGBX_RGBA,
                bandwidth=RecvBandwidth.highest,
            )
            self._video_frame = VideoFrameSync()
            self._receiver.frame_sync.set_video_frame(self._video_frame)
            if AudioFrameSync is not None:
                self._audio_frame = AudioFrameSync()
                self._receiver.frame_sync.set_audio_frame(self._audio_frame)
            self.refresh_sources()
            return True
        except Exception as exc:
            msg = str(exc)
            self._finder = None
            self._receiver = None
            self._video_frame = None
            if 'ndi' in msg.lower() or 'dll' in msg.lower():
                self._last_error = f'{msg} — install NDI Runtime: https://ndi.link/NDIRedistV6'
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
        self._audio_frame = None
        self._connected = False
        self._has_video = False

    def _on_finder_change(self) -> None:
        try:
            self._available_sources = list(self._finder.get_source_names() or [])
        except Exception:
            self._available_sources = self._available_sources or []
        if self._pending_connect and not self._connected and self._desired_source in self._available_sources:
            self._try_connect_throttled()

    def _try_connect_throttled(self) -> None:
        now = time.time()
        if now - self._last_connect_try < self._retry_interval:
            return
        self._last_connect_try = now
        if self._desired_source:
            self._connect_to_source()

    def maintain_connection(self) -> None:
        if self._receiver is None:
            return
        if self._connected and not self._receiver.is_connected():
            self._connected = False
            self._has_video = False
            self._pending_connect = True
        if self._pending_connect and self._desired_source in self._available_sources:
            self._try_connect_throttled()

    def refresh_sources(self, *, wait_s: float = 0.0) -> list[str]:
        if self._finder is None:
            return []
        deadline = time.perf_counter() + max(0.0, wait_s)
        try:
            while True:
                self._available_sources = list(self._finder.get_source_names() or [])
                if self._available_sources or time.perf_counter() >= deadline:
                    break
                time.sleep(0.25)
        except Exception:
            self._available_sources = []
        return list(self._available_sources)

    def list_sources(self) -> list[str]:
        return list(self._available_sources)

    def select_source(self, name: str) -> bool:
        self._desired_source = (name or '').strip()
        if not self._desired_source or self._finder is None or self._receiver is None:
            self._connected = False
            self._has_video = False
            self._pending_connect = False
            return False
        self._pending_connect = True
        if self._desired_source not in self._available_sources:
            self.refresh_sources()
        if self._desired_source not in self._available_sources:
            self._last_error = f"NDI source '{self._desired_source}' not on LAN yet"
            return False
        return self._connect_to_source()

    def _connect_to_source(self) -> bool:
        if self._finder is None or self._receiver is None or not self._desired_source:
            return False
        try:
            source = self._finder.get_source(self._desired_source)
            if source is None:
                self._last_error = f"NDI source '{self._desired_source}' not found"
                self._connected = False
                self._has_video = False
                return False
            self._receiver.set_source(source)
            for _ in range(200):
                if self._receiver.is_connected():
                    self._connected = True
                    self._pending_connect = False
                    self._last_error = ''
                    for _ in range(150):
                        self._receiver.frame_sync.capture_video()
                        if min(self._video_frame.xres, self._video_frame.yres) > 0:
                            self._has_video = True
                            self.frame_width = int(self._video_frame.xres)
                            self.frame_height = int(self._video_frame.yres)
                            return True
                        time.sleep(0.01)
                    return True
                time.sleep(0.01)
            self._last_error = 'NDI receiver connection timeout'
            self._connected = False
            self._has_video = False
            return False
        except Exception as exc:
            self._last_error = str(exc)
            self._connected = False
            self._has_video = False
            return False

    def grab_bgr(self) -> np.ndarray | None:
        self.maintain_connection()
        if self._receiver is None or self._video_frame is None:
            return None
        if cv2 is None:
            self._last_error = 'opencv-python required for NDI frames'
            return None
        try:
            if not self._receiver.is_connected():
                self._connected = False
                self._has_video = False
                time.sleep(0.002)
                return None

            self._receiver.frame_sync.capture_video()
            if min(self._video_frame.xres, self._video_frame.yres) == 0:
                self._has_video = False
                time.sleep(0.002)
                return None

            self.frame_width = int(self._video_frame.xres)
            self.frame_height = int(self._video_frame.yres)
            self._has_video = True
            self._last_error = ''
            frame = np.frombuffer(self._video_frame, dtype=np.uint8).copy()
            frame = frame.reshape((self.frame_height, self.frame_width, 4))
            return cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        except Exception as exc:
            self._last_error = str(exc)
            self._has_video = False
            return None
