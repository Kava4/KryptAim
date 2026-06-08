"""KMBOX Net network mouse backend (Sunone-compatible settings)."""

from __future__ import annotations

import logging
import socket
import struct
import threading

logger = logging.getLogger('AimSync.Input.KmboxNet')


class KmboxNetInput:
    name = 'kmbox_net'

    def __init__(self, ip: str, port: str, uuid: str = 'DEADC0DE') -> None:
        self._ip = (ip or '10.42.42.42').strip()
        self._port = int(port or 1984)
        self._uuid = (uuid or 'DEADC0DE').strip()
        self._sock: socket.socket | None = None
        self._lock = threading.Lock()
        self._open = False
        self._spraying = False

    def connect(self) -> bool:
        self.disconnect()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(0.5)
            self._sock = sock
            self._open = True
            logger.info('KMBOX Net ready for %s:%s', self._ip, self._port)
            return True
        except OSError as exc:
            logger.warning('KMBOX Net connect failed: %s', exc)
            return False

    def disconnect(self) -> None:
        with self._lock:
            if self._sock is not None:
                try:
                    self._sock.close()
                except Exception:
                    pass
            self._sock = None
            self._open = False
            self._spraying = False

    def is_open(self) -> bool:
        return self._open and self._sock is not None

    def _send(self, payload: bytes) -> None:
        if not self.is_open() or self._sock is None:
            return
        with self._lock:
            try:
                self._sock.sendto(payload, (self._ip, self._port))
            except OSError as exc:
                logger.debug('KMBOX Net send failed: %s', exc)

    def move(self, dx: int, dy: int) -> None:
        if dx == 0 and dy == 0:
            return
        # Minimal move packet — device-specific; extend when hardware available for testing.
        payload = b'move' + struct.pack('<ii', int(dx), int(dy))
        self._send(payload)

    def press(self, button: str = 'LMB') -> None:
        if button.upper() not in ('LMB', 'LEFT'):
            return
        self._send(b'ld')

    def release(self, button: str = 'LMB') -> None:
        if button.upper() not in ('LMB', 'LEFT'):
            return
        self._send(b'lu')
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
