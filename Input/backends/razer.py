"""Razer rzctl.dll mouse backend (Sunone-compatible)."""

from __future__ import annotations

import ctypes
import logging
import sys
from pathlib import Path

logger = logging.getLogger('AimSync.Input.Razer')


class RazerInput:
    name = 'razer'

    def __init__(self, dll_path: str = '') -> None:
        self._dll_path = dll_path
        self._dll = None
        self._open = False
        self._spraying = False

    def _resolve_dll_path(self) -> Path:
        if self._dll_path:
            return Path(self._dll_path)
        if getattr(sys, 'frozen', False):
            base = Path(sys.executable).resolve().parent
        else:
            base = Path(__file__).resolve().parent.parent.parent
        for candidate in (base / 'rzctl.dll', base / 'Input' / 'vendor' / 'rzctl.dll'):
            if candidate.is_file():
                return candidate
        return base / 'rzctl.dll'

    def connect(self) -> bool:
        path = self._resolve_dll_path()
        if not path.is_file():
            logger.warning('Razer rzctl.dll not found: %s', path)
            return False
        try:
            dll = ctypes.WinDLL(str(path))
            init = getattr(dll, 'init', None)
            if init is not None:
                self._open = bool(init())
            else:
                mouse_open = getattr(dll, 'mouse_open', None)
                self._open = bool(mouse_open()) if mouse_open else False
            self._dll = dll
            return self._open
        except OSError as exc:
            logger.warning('Razer DLL load failed: %s', exc)
            return False

    def disconnect(self) -> None:
        if self._dll is not None:
            close = getattr(self._dll, 'mouse_close', None)
            if close is not None:
                try:
                    close()
                except Exception:
                    pass
        self._dll = None
        self._open = False
        self._spraying = False

    def is_open(self) -> bool:
        return self._open

    def move(self, dx: int, dy: int) -> None:
        if not self._open or self._dll is None or (dx == 0 and dy == 0):
            return
        move_fn = getattr(self._dll, 'mouse_move', None) or getattr(self._dll, 'moveR', None)
        if move_fn is not None:
            try:
                move_fn(int(dx), int(dy))
            except Exception as exc:
                logger.debug('Razer move failed: %s', exc)

    def press(self, button: str = 'LMB') -> None:
        if not self._open or self._dll is None or button.upper() not in ('LMB', 'LEFT'):
            return
        down = getattr(self._dll, 'mouse_down', None)
        if down is not None:
            try:
                down(1)
            except Exception:
                pass

    def release(self, button: str = 'LMB') -> None:
        if not self._open or self._dll is None or button.upper() not in ('LMB', 'LEFT'):
            return
        up = getattr(self._dll, 'mouse_up', None)
        if up is not None:
            try:
                up()
            except Exception:
                pass
        self._spraying = False

    def click(self, button: str = 'LMB', hold_ms: int = 20) -> None:
        self.press(button)
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
