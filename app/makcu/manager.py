"""Makcu bridge — hardware production path + optional dev software fallback."""

from __future__ import annotations

import threading
import time

from makcu import MouseButton, create_controller


class MakcuManager:
    controller = None
    button_states = {
        'LMB': False,
        'RMB': False,
        'MMB': False,
        'M4': False,
        'M5': False,
    }
    connection_lock = threading.Lock()
    is_connected_flag = False
    dev_mode = False
    last_error = ''
    _dev_allowed = False

    @classmethod
    def set_dev_allowed(cls, allowed: bool) -> None:
        cls._dev_allowed = allowed

    @staticmethod
    def is_hardware() -> bool:
        return MakcuManager.is_connected_flag and MakcuManager.controller is not None and not MakcuManager.dev_mode

    @staticmethod
    def is_connected() -> bool:
        return MakcuManager.is_hardware() or MakcuManager.dev_mode

    @staticmethod
    def connect():
        MakcuManager.last_error = ''
        MakcuManager.dev_mode = False
        with MakcuManager.connection_lock:
            if MakcuManager.controller is not None:
                MakcuManager.is_connected_flag = True
                return MakcuManager.controller
            try:
                MakcuManager.controller = create_controller(
                    debug=False,
                    auto_reconnect=True,
                )

                def on_button_event(button: MouseButton, pressed: bool) -> None:
                    if button == MouseButton.LEFT:
                        MakcuManager.button_states['LMB'] = pressed
                    elif button == MouseButton.RIGHT:
                        MakcuManager.button_states['RMB'] = pressed
                    elif button == MouseButton.MIDDLE:
                        MakcuManager.button_states['MMB'] = pressed
                    elif button == MouseButton.MOUSE4:
                        MakcuManager.button_states['M4'] = pressed
                    elif button == MouseButton.MOUSE5:
                        MakcuManager.button_states['M5'] = pressed

                MakcuManager.controller.set_button_callback(on_button_event)
                MakcuManager.controller.enable_button_monitoring(True)
                MakcuManager.is_connected_flag = True
                print('[MAKCU] Connected')
            except Exception as exc:
                MakcuManager.last_error = str(exc)
                print(f'[MAKCU] Connection error: {exc}')
                MakcuManager.is_connected_flag = False
                MakcuManager.controller = None
                if MakcuManager._dev_allowed:
                    MakcuManager.dev_mode = True
                    print('[MAKCU] Dev mode: using local mouse (SendInput) — not for dual-PC')
                    return object()
                return None
            return MakcuManager.controller

    @staticmethod
    def move_relative(dx: float, dy: float) -> bool:
        if not MakcuManager.is_connected() or MakcuManager.dev_mode:
            from app.input.dev_software import move_relative

            move_relative(int(round(dx)), int(round(dy)))
            return True
        if dx == 0 and dy == 0:
            return False
        try:
            MakcuManager.controller.move(int(round(dx)), int(round(dy)))
            return True
        except Exception as exc:
            MakcuManager.last_error = str(exc)
            print(f'[MAKCU] Move error: {exc}')
            MakcuManager.is_connected_flag = False
            return False

    @staticmethod
    def move_mouse_smoothly(dx: float, dy: float, steps: int = 20, duration: float = 0.05) -> bool:
        if not MakcuManager.is_connected():
            return False
        if dx == 0 and dy == 0:
            return False

        if MakcuManager.dev_mode:
            from app.input.dev_software import move_smoothly

            move_smoothly(dx, dy, steps=steps, duration=duration)
            return True

        def ease_out_quad(t: float) -> float:
            return t * (2.0 - t)

        mck = MakcuManager.controller
        step_delay = duration / steps
        try:
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
                    mck.move(move_x, move_y)
                time.sleep(step_delay)
            return True
        except Exception as exc:
            MakcuManager.last_error = str(exc)
            print(f'[MAKCU] Smooth move error: {exc}')
            MakcuManager.is_connected_flag = False
            return False

    @staticmethod
    def _mouse_button(button_name: str):
        mapping = {
            'LMB': MouseButton.LEFT,
            'RMB': MouseButton.RIGHT,
            'MMB': MouseButton.MIDDLE,
            'M4': MouseButton.MOUSE4,
            'M5': MouseButton.MOUSE5,
        }
        btn = mapping.get(button_name.upper())
        if btn is None:
            raise ValueError(f'Unsupported button: {button_name}')
        return btn

    @staticmethod
    def click(button_name: str = 'LMB', hold_ms: int = 20) -> bool:
        if not MakcuManager.is_connected():
            return False
        if MakcuManager.dev_mode:
            from app.input.dev_software import click_button

            click_button(button_name, hold_ms=hold_ms)
            return True
        try:
            btn = MakcuManager._mouse_button(button_name)
            MakcuManager.controller.press(btn)
            if hold_ms > 0:
                time.sleep(hold_ms / 1000.0)
            MakcuManager.controller.release(btn)
            return True
        except Exception as exc:
            MakcuManager.last_error = str(exc)
            print(f'[MAKCU] Click error: {exc}')
            MakcuManager.is_connected_flag = False
            return False

    @staticmethod
    def get_button_state(button_name: str) -> bool:
        if MakcuManager.dev_mode:
            from app.input.dev_software import get_button_state

            return get_button_state(button_name)
        return MakcuManager.button_states.get(button_name, False)

    @staticmethod
    def disconnect() -> None:
        with MakcuManager.connection_lock:
            if MakcuManager.controller:
                try:
                    MakcuManager.controller.disconnect()
                except Exception:
                    pass
            MakcuManager.controller = None
            MakcuManager.is_connected_flag = False
            MakcuManager.dev_mode = False


makcu_manager = MakcuManager()
