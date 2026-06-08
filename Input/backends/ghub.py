"""Logitech G Hub DLL mouse backend (Sunone ghub_mouse.dll protocol)."""

from __future__ import annotations

import ctypes
import logging
import sys
import threading
import time
from pathlib import Path

logger = logging.getLogger('AimSync.Input.GHub')


class GhubInput:
    name = 'ghub'

    def __init__(self, dll_path: str = '') -> None:
        self._lock = threading.Lock()
        self._dll = None
        self._open = False
        self._move_r = None
        self._press = None
        self._release = None
        self._mouse_close = None
        self._dll_path = dll_path
        self._spraying = False

    def _resolve_dll_path(self) -> Path:
        if self._dll_path:
            return Path(self._dll_path)
        if getattr(sys, 'frozen', False):
            base = Path(sys.executable).resolve().parent
        else:
            base = Path(__file__).resolve().parent.parent.parent
        for candidate in (
            base / 'ghub_mouse.dll',
            base / 'Input' / 'vendor' / 'ghub_mouse.dll',
        ):
            if candidate.is_file():
                return candidate
        return base / 'ghub_mouse.dll'

    def connect(self) -> bool:
        path = self._resolve_dll_path()
        if not path.is_file():
            logger.warning('G Hub DLL not found: %s', path)
            self._open = False
            return False
        try:
            dll = ctypes.WinDLL(str(path))
            mouse_open = getattr(dll, 'mouse_open', None)
            if mouse_open is None:
                logger.warning('ghub_mouse.dll missing mouse_open export')
                return False
            self._open = bool(mouse_open())
            self._move_r = getattr(dll, 'moveR', None)
            self._press = getattr(dll, 'press', None)
            self._release = getattr(dll, 'release', None)
            self._mouse_close = getattr(dll, 'mouse_close', None)
            self._dll = dll
            if not self._open:
                logger.warning('G Hub mouse_open returned false')
            return self._open
        except OSError as exc:
            logger.warning('Failed to load G Hub DLL: %s', exc)
            self._open = False
            return False

    def disconnect(self) -> None:
        with self._lock:
            if self._dll is not None and self._mouse_close is not None:
                try:
                    self._mouse_close()
                except Exception:
                    pass
            self._dll = None
            self._open = False
            self._spraying = False

    def is_open(self) -> bool:
        return self._open

    def move(self, dx: int, dy: int) -> None:
        if dx == 0 and dy == 0 or not self._open:
            return
        with self._lock:
            if self._move_r is not None:
                try:
                    self._move_r(int(dx), int(dy))
                except Exception as exc:
                    logger.debug('G Hub moveR failed: %s', exc)

    def press(self, button: str = 'LMB') -> None:
        if not self._open or button.upper() not in ('LMB', 'LEFT'):
            return
        with self._lock:
            if self._press is not None:
                try:
                    self._press(1)
                except Exception as exc:
                    logger.debug('G Hub press failed: %s', exc)

    def release(self, button: str = 'LMB') -> None:
        if not self._open or button.upper() not in ('LMB', 'LEFT'):
            return
        with self._lock:
            if self._release is not None:
                try:
                    self._release()
                except Exception as exc:
                    logger.debug('G Hub release failed: %s', exc)
            self._spraying = False

    def click(self, button: str = 'LMB', hold_ms: int = 20) -> None:
        self.press(button)
        if hold_ms > 0:
            time.sleep(hold_ms / 1000.0)
        self.release(button)

    def hold_left(self) -> None:
        if self._spraying:
            return
        self.press('LMB')
        self._spraying = True

    def release_left(self) -> None:
        if not self._spraying:
            return
        self.release('LMB')

    def reset_spray(self) -> None:
        self.release_left()

    def get_button_state(self, key_name: str) -> bool:
        from Input.backends.win32 import Win32Input

        return Win32Input().get_button_state(key_name)
