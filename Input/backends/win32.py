"""Win32 SendInput mouse backend (standalone — does not modify Makcu/software_manager)."""

from __future__ import annotations

import ctypes
import logging
import threading
import time
from ctypes import wintypes

logger = logging.getLogger('AimSync.Input.Win32')

_user32 = ctypes.windll.user32

VK_LBUTTON = 0x01
VK_RBUTTON = 0x02
VK_MBUTTON = 0x04
VK_XBUTTON1 = 0x05
VK_XBUTTON2 = 0x06

MOUSE_VK = {
    'LMB': VK_LBUTTON,
    'RMB': VK_RBUTTON,
    'MMB': VK_MBUTTON,
    'M4': VK_XBUTTON1,
    'M5': VK_XBUTTON2,
}

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100
XBUTTON1 = 0x0001
XBUTTON2 = 0x0002

ULONG_PTR = wintypes.ULONG if ctypes.sizeof(ctypes.c_void_p) == 4 else ctypes.c_ulonglong


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ('dx', wintypes.LONG),
        ('dy', wintypes.LONG),
        ('mouseData', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ULONG_PTR),
    ]


class INPUT(ctypes.Structure):
    class _INPUT_UNION(ctypes.Union):
        _fields_ = [('mi', MOUSEINPUT)]

    _anonymous_ = ('u',)
    _fields_ = [
        ('type', wintypes.DWORD),
        ('u', _INPUT_UNION),
    ]


def _button_flags(button: str, down: bool) -> tuple[int, int]:
    key = button.upper()
    if key in ('LMB', 'LEFT'):
        return (MOUSEEVENTF_LEFTDOWN if down else MOUSEEVENTF_LEFTUP), 0
    if key in ('RMB', 'RIGHT'):
        return (MOUSEEVENTF_RIGHTDOWN if down else MOUSEEVENTF_RIGHTUP), 0
    if key in ('MMB', 'MIDDLE'):
        return (MOUSEEVENTF_MIDDLEDOWN if down else MOUSEEVENTF_MIDDLEUP), 0
    if key in ('M4', 'MOUSE4'):
        flag = MOUSEEVENTF_XDOWN if down else MOUSEEVENTF_XUP
        return flag, XBUTTON1
    if key in ('M5', 'MOUSE5'):
        flag = MOUSEEVENTF_XDOWN if down else MOUSEEVENTF_XUP
        return flag, XBUTTON2
    return (MOUSEEVENTF_LEFTDOWN if down else MOUSEEVENTF_LEFTUP), 0


class Win32Input:
    name = 'win32'

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._spraying = False

    def is_open(self) -> bool:
        return True

    def connect(self) -> bool:
        return True

    def disconnect(self) -> None:
        self.release('LMB')

    def _send(self, flags: int, dx: int = 0, dy: int = 0, data: int = 0) -> bool:
        event = INPUT(
            type=INPUT_MOUSE,
            mi=MOUSEINPUT(
                dx=int(dx),
                dy=int(dy),
                mouseData=int(data),
                dwFlags=int(flags),
                time=0,
                dwExtraInfo=0,
            ),
        )
        with self._lock:
            inserted = _user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT))
        if inserted != 1:
            logger.debug('SendInput rejected flags=%s dx=%s dy=%s', flags, dx, dy)
            return False
        return True

    def move(self, dx: int, dy: int) -> None:
        if dx == 0 and dy == 0:
            return
        if not self._send(MOUSEEVENTF_MOVE, dx, dy):
            with self._lock:
                _user32.mouse_event(MOUSEEVENTF_MOVE, int(dx), int(dy), 0, 0)

    def press(self, button: str = 'LMB') -> None:
        flags, data = _button_flags(button, True)
        self._send(flags, data=data)

    def release(self, button: str = 'LMB') -> None:
        flags, data = _button_flags(button, False)
        self._send(flags, data=data)
        if button.upper() in ('LMB', 'LEFT'):
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
        vk = MOUSE_VK.get(key_name.upper())
        if vk is None:
            return False
        with self._lock:
            if _user32.GetAsyncKeyState(vk) & 0x8000:
                return True
            return bool(_user32.GetKeyState(vk) & 0x8000)
