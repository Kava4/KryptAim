"""Windows SendInput fallback — single-PC dev/test only (not dual-PC production)."""

from __future__ import annotations

import sys
import time

if sys.platform != 'win32':
    raise RuntimeError('Dev software input is Windows-only')

import ctypes

user32 = ctypes.windll.user32

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100
_XBUTTON1 = 0x0001
_XBUTTON2 = 0x0002
_VK = {
    'LMB': 0x01,
    'RMB': 0x02,
    'MMB': 0x04,
    'M4': 0x05,
    'M5': 0x06,
}


def get_button_state(button_name: str) -> bool:
    vk = _VK.get(button_name)
    if vk is None:
        return False
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def move_relative(dx: int, dy: int) -> None:
    if dx == 0 and dy == 0:
        return
    user32.mouse_event(MOUSEEVENTF_MOVE, int(dx), int(dy), 0, 0)


def _button_events(button_name: str, down: bool) -> tuple[int, int]:
    name = button_name.upper()
    if name == 'LMB':
        return (MOUSEEVENTF_LEFTDOWN, 0) if down else (MOUSEEVENTF_LEFTUP, 0)
    if name == 'RMB':
        return (MOUSEEVENTF_RIGHTDOWN, 0) if down else (MOUSEEVENTF_RIGHTUP, 0)
    if name == 'MMB':
        return (MOUSEEVENTF_MIDDLEDOWN, 0) if down else (MOUSEEVENTF_MIDDLEUP, 0)
    if name == 'M4':
        return (MOUSEEVENTF_XDOWN, _XBUTTON1) if down else (MOUSEEVENTF_XUP, _XBUTTON1)
    if name == 'M5':
        return (MOUSEEVENTF_XDOWN, _XBUTTON2) if down else (MOUSEEVENTF_XUP, _XBUTTON2)
    raise ValueError(f'Unsupported button: {button_name}')


def press_button(button_name: str) -> None:
    flags, data = _button_events(button_name, True)
    user32.mouse_event(flags, 0, 0, data, 0)


def release_button(button_name: str) -> None:
    flags, data = _button_events(button_name, False)
    user32.mouse_event(flags, 0, 0, data, 0)


def click_button(button_name: str = 'LMB', hold_ms: int = 20) -> None:
    press_button(button_name)
    if hold_ms > 0:
        time.sleep(hold_ms / 1000.0)
    release_button(button_name)


def move_smoothly(dx: float, dy: float, steps: int = 20, duration: float = 0.05) -> None:
    if dx == 0 and dy == 0:
        return

    def ease_out_quad(t: float) -> float:
        return t * (2.0 - t)

    step_delay = duration / steps
    accumulated_x = 0.0
    accumulated_y = 0.0
    for i in range(steps):
        t = (i + 1) / steps
        eased = ease_out_quad(t)
        move_x = round(dx * eased - accumulated_x)
        move_y = round(dy * eased - accumulated_y)
        accumulated_x += move_x
        accumulated_y += move_y
        if move_x or move_y:
            move_relative(move_x, move_y)
        time.sleep(step_delay)
