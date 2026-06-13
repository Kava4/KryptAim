"""Aim assist — move toward closest detection (eventuri-style sens scale)."""

from __future__ import annotations

import math

from app.ai.capture.backend import FrameContext
from app.ai.types import Prediction
from app.ai.trigger import trigger_weapon_allowed
from app.makcu.manager import makcu_manager


def sensitivity_scale(in_game_sens: float) -> float:
    sens = max(0.1, float(in_game_sens or 1.25))
    return 1.07437623 * math.pow(sens, -0.9936827126)


def aim_armed(config: dict) -> bool:
    if not config.get('ai_enabled') or not config.get('ai_aim_enabled'):
        return False
    if config.get('ai_aim_always_on') or config.get('ai_trigger_always_on'):
        return True
    key = (config.get('ai_aim_keybind') or config.get('ai_trigger_keybind') or 'M4').strip()
    if key.lower() == 'none':
        return True
    return makcu_manager.get_button_state(key)


def aim_delta_for_target(
    config: dict,
    target: Prediction,
    frame: FrameContext,
) -> tuple[float, float] | None:
    """Gaming-PC pixel delta from crosshair to target center."""
    scale = frame.region.width / max(frame.image_size, 1)
    aim_x = frame.region.left + target.screen_center_x * scale
    aim_y = frame.region.top + target.screen_center_y * scale
    dx = aim_x - frame.crosshair_x
    dy = aim_y - frame.crosshair_y

    sens = float(
        config.get('recoil_cs2_settings', {}).get('cs2_sensitivity', 1.25) or 1.25
    )
    dist = sensitivity_scale(sens)
    dx *= dist
    dy *= dist

    speed = float(config.get('ai_aim_speed', 1.0) or 1.0)
    dx *= speed
    dy *= speed
    return dx, dy


class AimController:
    def __init__(self) -> None:
        self.last_block_reason = ''
        self._residual_dx = 0.0
        self._residual_dy = 0.0

    def reset_tracking(self) -> None:
        self._residual_dx = 0.0
        self._residual_dy = 0.0

    def update_correction(
        self,
        config: dict,
        *,
        armed: bool,
        targets: list[Prediction] | None,
        frame: FrameContext | None,
    ) -> None:
        """Called once per YOLO frame — sets move vector toward best target."""
        if not config.get('ai_enabled') or not config.get('ai_aim_enabled'):
            self.last_block_reason = 'aim_off'
            self.reset_tracking()
            return
        if not trigger_weapon_allowed(config):
            self.last_block_reason = 'spray_recoil'
            self.reset_tracking()
            return
        if not armed:
            self.last_block_reason = 'aim_not_armed'
            self.reset_tracking()
            return
        pool = list(targets or [])
        if not pool or frame is None:
            self.last_block_reason = 'no_target'
            self.reset_tracking()
            return

        min_conf = float(config.get('ai_trigger_min_conf', 0.35))
        pool = [t for t in pool if t.confidence >= min_conf]
        if not pool:
            self.last_block_reason = 'low_conf'
            self.reset_tracking()
            return

        heads = [t for t in pool if t.is_head]
        pool_for_aim = heads if heads else pool
        best = min(pool_for_aim, key=lambda t: t.image_dist)
        fov_limit = float(config.get('ai_aim_max_px', 280) or 280)
        if best.image_dist > fov_limit:
            self.last_block_reason = 'outside_fov'
            self.reset_tracking()
            return

        delta = aim_delta_for_target(config, best, frame)
        if delta is None:
            self.last_block_reason = 'no_delta'
            self.reset_tracking()
            return
        dx, dy = delta
        if abs(dx) < 0.5 and abs(dy) < 0.5:
            self.last_block_reason = 'on_target'
            self.reset_tracking()
            return

        self._residual_dx = dx
        self._residual_dy = dy
        self.last_block_reason = 'tracking'

    def step(self, *, armed: bool) -> None:
        """Fast tick — apply a slice of the pending correction (sticky between inferences)."""
        if not armed or (abs(self._residual_dx) < 0.5 and abs(self._residual_dy) < 0.5):
            return
        fraction = 0.45
        step_x = self._residual_dx * fraction
        step_y = self._residual_dy * fraction
        self._residual_dx -= step_x
        self._residual_dy -= step_y
        if abs(step_x) >= 0.5 or abs(step_y) >= 0.5:
            makcu_manager.move_relative(step_x, step_y)
