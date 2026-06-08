"""Route mouse actions to alt backends when method != makcu."""

from __future__ import annotations

import logging
import threading

from Config.config_manager import load_config
from Input.factory import create_backend
from Input.methods import method_display_name, resolve_mouse_input_method, use_alt_input
from Input.protocol import MouseInputBackend

logger = logging.getLogger('AimSync.Input.Router')


class InputRouter:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._backend: MouseInputBackend | None = None
        self._method_key = ''
        self._last_error = ''

    def reload(self, config: dict | None = None) -> None:
        cfg = config or load_config()
        method = resolve_mouse_input_method(cfg)
        with self._lock:
            if self._backend is not None:
                try:
                    self._backend.disconnect()
                except Exception:
                    pass
            self._backend = None
            self._method_key = ''
            if method == 'makcu':
                self._last_error = ''
                return
            try:
                self._backend = create_backend(method, cfg)
                self._method_key = method
                if not self._backend.is_open():
                    self._last_error = f'{method_display_name(method)} not connected'
                else:
                    self._last_error = ''
            except Exception as exc:
                logger.warning('Alt input backend failed (%s): %s', method, exc)
                self._last_error = str(exc)

    def _backend_or_reload(self) -> MouseInputBackend | None:
        cfg = load_config()
        if not use_alt_input(cfg):
            return None
        method = resolve_mouse_input_method(cfg)
        with self._lock:
            if method != self._method_key or self._backend is None:
                self.reload(cfg)
            return self._backend

    def status(self, config: dict | None = None) -> dict:
        cfg = config or load_config()
        method = resolve_mouse_input_method(cfg)
        if method == 'makcu':
            return {
                'method': method,
                'method_label': method_display_name(method),
                'using_alt': False,
                'connected': False,
                'last_error': '',
            }
        backend = self._backend_or_reload()
        connected = bool(backend and backend.is_open())
        return {
            'method': method,
            'method_label': method_display_name(method),
            'using_alt': True,
            'connected': connected,
            'last_error': self._last_error,
        }

    def move(self, dx: int, dy: int) -> None:
        backend = self._backend_or_reload()
        if backend is None:
            return
        backend.move(dx, dy)

    def press(self, button: str = 'LMB') -> None:
        backend = self._backend_or_reload()
        if backend is None:
            return
        backend.press(button)

    def release(self, button: str = 'LMB') -> None:
        backend = self._backend_or_reload()
        if backend is None:
            return
        backend.release(button)

    def click(self, button: str = 'LMB', hold_ms: int = 20) -> None:
        backend = self._backend_or_reload()
        if backend is None:
            return
        if hasattr(backend, 'click'):
            backend.click(button, hold_ms=hold_ms)
            return
        backend.press(button)
        backend.release(button)

    def hold_left(self) -> None:
        backend = self._backend_or_reload()
        if backend is None:
            return
        if hasattr(backend, 'hold_left'):
            backend.hold_left()
            return
        backend.press('LMB')

    def release_left(self) -> None:
        backend = self._backend_or_reload()
        if backend is None:
            return
        if hasattr(backend, 'release_left'):
            backend.release_left()
            return
        backend.release('LMB')

    def reset_spray(self) -> None:
        backend = self._backend_or_reload()
        if backend is None:
            return
        if hasattr(backend, 'reset_spray'):
            backend.reset_spray()
            return
        backend.release('LMB')

    def get_button_state(self, key_name: str) -> bool:
        backend = self._backend_or_reload()
        if backend is None:
            from Input.backends.win32 import Win32Input

            return Win32Input().get_button_state(key_name)
        return backend.get_button_state(key_name)

    def move_smooth_steps(self, dx: int, dy: int, segments: int = 6) -> None:
        """Segmented move for alt backends without hardware bezier."""
        if dx == 0 and dy == 0:
            return
        segments = max(2, int(segments))
        rem_x, rem_y = int(dx), int(dy)
        for i in range(segments):
            if i < segments - 1:
                step_x = int(round(dx / segments))
                step_y = int(round(dy / segments))
            else:
                step_x, step_y = rem_x, rem_y
            rem_x -= step_x
            rem_y -= step_y
            if step_x or step_y:
                self.move(step_x, step_y)


input_router = InputRouter()
