"""Auto trigger click logic."""

from __future__ import annotations

import time

from Config.config_manager import load_config
from Input.methods import use_alt_input
from Input.router import input_router
from Makcu.makcu_manager import makcu_manager

from AI.Engine.capture import ScreenCapture
from AI.Engine.settings import AiSettings
from AI.Engine.target import Prediction


class TriggerController:
    def __init__(self, settings: AiSettings, capture: ScreenCapture) -> None:
        self._settings = settings
        self._capture = capture
        self._last_click = 0.0
        self._click_hold_ms = 20
        self._in_zone_since = 0.0
        self.last_fire_at = 0.0
        self.last_block_reason = ''

    def reset_spray(self, config: dict | None = None) -> None:
        cfg = config if config is not None else load_config()
        if use_alt_input(cfg):
            input_router.reset_spray()
        else:
            makcu_manager.reset_spray()
        self._in_zone_since = 0.0

    def _auto_trigger_enabled(self, config: dict) -> bool:
        """Trigger always on in Setup arms triggerbot even if profile Auto Trigger was left off."""
        if bool(config.get('ai_trigger_always_on')):
            return True
        if self._settings.toggles.get('Auto Trigger'):
            return True
        return bool(config.get('ai_trigger_enabled'))

    def _crosshair_in_trigger_zone(
        self,
        target: Prediction,
        *,
        crosshair_x: int,
        crosshair_y: int,
        radius_px: int,
    ) -> bool:
        if radius_px <= 0:
            return True
        dx = target.screen_center_x - crosshair_x
        dy = target.screen_center_y - crosshair_y
        if (dx * dx + dy * dy) <= radius_px * radius_px:
            return True
        left, top, w, h = target.detection_box
        return left <= crosshair_x <= left + w and top <= crosshair_y <= top + h

    def _crosshair_on_target(
        self,
        target: Prediction,
        *,
        crosshair_x: int,
        crosshair_y: int,
    ) -> bool:
        left, top, w, h = target.detection_box
        return left <= crosshair_x <= left + w and top <= crosshair_y <= top + h

    def run_trigger(
        self,
        target: Prediction | None,
        trigger_active: bool,
        config: dict | None = None,
        *,
        crosshair_x: int | None = None,
        crosshair_y: int | None = None,
    ) -> None:
        cfg = config or {}
        if not self._auto_trigger_enabled(cfg):
            self.last_block_reason = 'auto_trigger_off'
            self.reset_spray()
            self._in_zone_since = 0.0
            return
        if not trigger_active:
            self.last_block_reason = 'trigger_not_armed'
            self.reset_spray()
            self._in_zone_since = 0.0
            return

        min_conf = float(cfg.get('ai_trigger_min_conf', 0.35))
        if target is not None and target.confidence < min_conf:
            self.last_block_reason = 'low_confidence'
            self.reset_spray()
            self._in_zone_since = 0.0
            return

        radius_px = int(cfg.get('ai_trigger_radius_px', 20) or 20)
        in_radius = True
        if target is not None and crosshair_x is not None and crosshair_y is not None:
            in_radius = self._crosshair_in_trigger_zone(
                target,
                crosshair_x=crosshair_x,
                crosshair_y=crosshair_y,
                radius_px=radius_px,
            )
            if not in_radius:
                self.last_block_reason = 'outside_trigger_zone'
                self.reset_spray()
                self._in_zone_since = 0.0
                return

        if target is None:
            self.last_block_reason = 'no_target'
            self._in_zone_since = 0.0
            return

        linger_ms = int(cfg.get('ai_trigger_linger_ms', 0) or 0)
        if linger_ms > 0 and in_radius:
            now = time.time()
            if self._in_zone_since <= 0:
                self._in_zone_since = now
            if (now - self._in_zone_since) * 1000.0 < linger_ms:
                return
        else:
            self._in_zone_since = 0.0

        if self._settings.toggles['Spray Mode']:
            if (
                self._settings.toggles['Cursor Check']
                and target is not None
                and crosshair_x is not None
                and crosshair_y is not None
                and not self._crosshair_on_target(
                    target, crosshair_x=crosshair_x, crosshair_y=crosshair_y,
                )
            ):
                self.last_block_reason = 'cursor_check'
                self.reset_spray()
                return
            self._fire_hold_left(cfg)
            self.last_fire_at = time.time()
            self.last_block_reason = ''
            return

        if (
            self._settings.toggles['Cursor Check']
            and target is not None
            and crosshair_x is not None
            and crosshair_y is not None
            and not self._crosshair_on_target(
                target, crosshair_x=crosshair_x, crosshair_y=crosshair_y,
            )
        ):
            self.last_block_reason = 'cursor_check'
            return

        delay_ms = int(cfg.get('ai_trigger_delay_ms', 0) or 0)
        cooldown_ms = int(cfg.get('ai_trigger_cooldown_ms', 0) or 0)
        delay = max(
            float(self._settings.sliders['Auto Trigger Delay']),
            delay_ms / 1000.0,
            cooldown_ms / 1000.0,
        )
        now = time.time()
        if self._last_click and (now - self._last_click) < delay:
            self.last_block_reason = 'cooldown'
            return
        hold_ms = int(cfg.get('ai_trigger_click_hold_ms', self._click_hold_ms) or self._click_hold_ms)
        self._fire_click(cfg, hold_ms=max(5, min(hold_ms, 40)))
        self._last_click = now
        self.last_fire_at = now
        self.last_block_reason = ''

    def _fire_hold_left(self, config: dict) -> None:
        if use_alt_input(config):
            input_router.hold_left()
            return
        makcu_manager.hold_left()

    def _fire_click(self, config: dict, *, hold_ms: int) -> None:
        if use_alt_input(config):
            input_router.click('LMB', hold_ms=hold_ms)
            return
        makcu_manager.click('LMB', hold_ms=hold_ms)
