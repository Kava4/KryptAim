"""Arduino / serial mouse bridge (Sunone Arduino.cpp text protocol)."""

from __future__ import annotations

import logging
import threading
from typing import Literal

logger = logging.getLogger('AimSync.Input.Arduino')

ProtocolKind = Literal['legacy', 'teensy41']


def _split_axis(value: int) -> list[int]:
    sign = -1 if value < 0 else 1
    remaining = abs(int(value))
    if remaining == 0:
        return [0]
    parts: list[int] = []
    while remaining > 127:
        parts.append(sign * 127)
        remaining -= 127
    if remaining:
        parts.append(sign * remaining)
    return parts


class ArduinoInput:
    name = 'arduino'

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        *,
        protocol: ProtocolKind = 'legacy',
        enable_keys: bool = False,
    ) -> None:
        self._port = (port or '').strip()
        self._baudrate = max(9600, int(baudrate or 115200))
        self._protocol = protocol
        self._enable_keys = enable_keys
        self._serial = None
        self._lock = threading.Lock()
        self._open = False
        self._spraying = False
        self._button_mask = 0

    def connect(self) -> bool:
        if not self._port or self._port.upper() == 'COM0':
            logger.warning('Arduino port not configured')
            return False
        try:
            import serial

            ser = serial.Serial(self._port, self._baudrate, timeout=0.1)
            self._serial = ser
            self._open = ser.is_open
            if self._open:
                logger.info('Arduino connected on %s @ %s', self._port, self._baudrate)
            return self._open
        except ImportError:
            logger.warning('pyserial not installed — pip install pyserial')
            return False
        except Exception as exc:
            logger.warning('Arduino connect failed (%s): %s', self._port, exc)
            return False

    def disconnect(self) -> None:
        with self._lock:
            if self._serial is not None:
                try:
                    self._serial.close()
                except Exception:
                    pass
            self._serial = None
            self._open = False
            self._spraying = False

    def is_open(self) -> bool:
        return self._open and self._serial is not None and getattr(self._serial, 'is_open', False)

    def _write(self, data: str) -> None:
        if not self.is_open() or self._serial is None:
            return
        with self._lock:
            try:
                self._serial.write(data.encode('ascii', errors='ignore'))
            except Exception as exc:
                logger.debug('Arduino write failed: %s', exc)
                self._open = False

    def move(self, dx: int, dy: int) -> None:
        if not self.is_open() or (dx == 0 and dy == 0):
            return
        if self._protocol == 'teensy41':
            self._write(f'move {int(dx)} {int(dy)} 0 0\n')
            return
        x_parts = _split_axis(dx)
        y_parts = _split_axis(dy)
        count = max(len(x_parts), len(y_parts))
        while len(x_parts) < count:
            x_parts.append(0)
        while len(y_parts) < count:
            y_parts.append(0)
        for sx, sy in zip(x_parts, y_parts):
            self._write(f'm{sx},{sy}\n')

    def press(self, button: str = 'LMB') -> None:
        if button.upper() not in ('LMB', 'LEFT'):
            return
        if self._protocol == 'teensy41':
            self._button_mask |= 1
            self._write(f'buttons {self._button_mask}\n')
        else:
            self._write('p\n')

    def release(self, button: str = 'LMB') -> None:
        if button.upper() not in ('LMB', 'LEFT'):
            return
        if self._protocol == 'teensy41':
            self._button_mask &= ~1
            self._write(f'buttons {self._button_mask}\n')
        else:
            self._write('r\n')
        self._spraying = False

    def click(self, button: str = 'LMB', hold_ms: int = 20) -> None:
        if self._protocol == 'teensy41':
            self.press(button)
            self.release(button)
            return
        self._write('c\n')

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
