"""CS2 recoil engine."""

from __future__ import annotations

import random
import time

from app.core.config import load_config, save_config
from app.makcu.manager import makcu_manager
from app.recoil.weapon_data import WeaponData

PATTERN_BASELINE = 1.25
CONFIG_RELOAD_INTERVAL = 1.0

_config_cache: dict | None = None
_config_loaded_at = 0.0
_shot_count = 0
_total_y_movement = 0.0
_lmb_was_pressed = False
_keybind_was_pressed = False
_timed_deadline: float | None = None


def reset_recoil_state() -> None:
    global _shot_count, _total_y_movement, _lmb_was_pressed, _timed_deadline
    _shot_count = 0
    _total_y_movement = 0.0
    _lmb_was_pressed = False
    _timed_deadline = None


def invalidate_config_cache() -> None:
    global _config_cache
    _config_cache = None


def get_config() -> dict:
    global _config_cache, _config_loaded_at
    now = time.time()
    if _config_cache is None or (now - _config_loaded_at) >= CONFIG_RELOAD_INTERVAL:
        _config_cache = load_config()
        _config_loaded_at = now
    return _config_cache


def _jitter(value: float, strength: float) -> float:
    return value + random.uniform(-strength, strength)


def _scale_step(dx: float, dy: float, sensitivity: float) -> tuple[float, float]:
    scalar = PATTERN_BASELINE / sensitivity
    return float(dx) * scalar, float(dy) * scalar


def _apply_controls(config: dict, x: float, y: float) -> tuple[float, float]:
    x_control = float(config.get('recoil_x_control', 100)) / 100.0
    y_control = float(config.get('recoil_y_control', 100)) / 100.0
    return x * x_control, y * y_control


def run_recoil() -> None:
    global _shot_count, _total_y_movement, _lmb_was_pressed, _keybind_was_pressed
    global _config_cache, _timed_deadline

    config = get_config()

    keybind = config.get('recoil_keybind', 'M4')
    keybind_pressed = makcu_manager.get_button_state(keybind)
    if keybind_pressed and not _keybind_was_pressed:
        config['recoil_enabled'] = not config['recoil_enabled']
        save_config(config)
        _config_cache = None
    _keybind_was_pressed = keybind_pressed

    if not config['recoil_enabled']:
        reset_recoil_state()
        time.sleep(0.05)
        return

    lmb_pressed = makcu_manager.get_button_state('LMB')

    if not lmb_pressed and _lmb_was_pressed and _total_y_movement != 0:
        if config.get('recoil_return_crosshair', False):
            makcu_manager.move_mouse_smoothly(0, -_total_y_movement)
        reset_recoil_state()
        time.sleep(0.02)
        return

    if not lmb_pressed:
        reset_recoil_state()
        time.sleep(0.02)
        return

    if not _lmb_was_pressed:
        _shot_count = 0
        _total_y_movement = 0.0
        _lmb_was_pressed = True

    if config.get('recoil_require_rmb') and not makcu_manager.get_button_state('RMB'):
        time.sleep(0.02)
        return

    cs2 = config.get('recoil_cs2_settings') or {}
    weapon_id = cs2.get('cs2_weapon', 'assault_rifle')
    pattern = WeaponData.get_pattern(weapon_id)

    sensitivity = float(cs2.get('cs2_sensitivity', PATTERN_BASELINE))
    if sensitivity <= 0:
        sensitivity = PATTERN_BASELINE

    if _shot_count >= len(pattern):
        time.sleep(0.02)
        return

    step_index = _shot_count
    dx, dy, delay = pattern[step_index]
    _shot_count += 1

    x, y = _scale_step(dx, dy, sensitivity)
    x, y = WeaponData.apply_tail_tune(weapon_id, step_index, len(pattern), x, y)
    if config.get('recoil_randomisation', False):
        strength = float(config.get('recoil_random_strength', 0.0))
        x = _jitter(x, strength)
        y = _jitter(y, strength)

    actual_x, actual_y = _apply_controls(config, x, y)
    profile = WeaponData.get_profile(weapon_id)

    if profile == 'timed':
        if step_index == 0:
            _timed_deadline = time.perf_counter()
        if actual_x or actual_y:
            makcu_manager.move_relative(actual_x, actual_y)
        _total_y_movement += actual_y
        if delay > 0:
            if _timed_deadline is None:
                _timed_deadline = time.perf_counter()
            _timed_deadline += float(delay)
            remaining = _timed_deadline - time.perf_counter()
            if remaining > 0:
                time.sleep(remaining)
        return

    if profile == 'spray':
        if delay > 0:
            time.sleep(float(delay))
        if actual_x or actual_y:
            makcu_manager.move_relative(actual_x, actual_y)
        _total_y_movement += actual_y
        return

    start = time.perf_counter()
    makcu_manager.move_mouse_smoothly(actual_x, actual_y)
    elapsed = time.perf_counter() - start
    _total_y_movement += actual_y
    remaining = float(delay) - elapsed
    if remaining > 0:
        time.sleep(remaining)
