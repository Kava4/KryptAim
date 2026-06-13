"""Auto trigger — fires LMB when a detection is inside the radius."""

from __future__ import annotations

import random
import time

from app.ai.types import Prediction
from app.makcu.manager import makcu_manager


def _cfg_int(config: dict, key: str, default: int) -> int:
    raw = config.get(key)
    if raw is None:
        return default
    return int(float(raw))


def _now_ms() -> float:
    return time.perf_counter() * 1000.0


def trigger_weapon_allowed(config: dict) -> bool:
    """Trigger is for pistol / sniper sessions — not while spray recoil is active."""
    if not config.get('ai_trigger_spray_block', True):
        return True
    return not bool(config.get('recoil_enabled'))


def trigger_armed(config: dict) -> bool:
    if not config.get('ai_enabled') or not config.get('ai_trigger_enabled'):
        return False
    if not trigger_weapon_allowed(config):
        return False
    if config.get('ai_trigger_always_on'):
        return True
    key = (config.get('ai_trigger_keybind') or 'M4').strip()
    if key.lower() == 'none':
        return True
    return makcu_manager.get_button_state(key)


class TriggerController:
    def __init__(self) -> None:
        self._last_click_ms = 0.0
        self._in_zone_since_ms = 0.0
        self.last_fire_at = 0.0
        self.last_block_reason = ''
        self.last_in_zone_count = 0
        self._rng = random.Random()

    def reset(self) -> None:
        self._in_zone_since_ms = 0.0

    def evaluate(
        self,
        config: dict,
        *,
        armed: bool,
        targets: list[Prediction] | None = None,
    ) -> None:
        if not config.get('ai_enabled') or not config.get('ai_trigger_enabled'):
            self.last_block_reason = 'trigger_off'
            self.reset()
            return
        if not trigger_weapon_allowed(config):
            self.last_block_reason = 'spray_recoil'
            self.reset()
            return
        if not armed:
            self.last_block_reason = 'not_armed'
            self.reset()
            return

        pool = list(targets or [])
        if not pool:
            self.last_block_reason = 'no_target'
            self.reset()
            return

        min_conf = float(config.get('ai_trigger_min_conf', 0.35))
        radius_px = float(_cfg_int(config, 'ai_trigger_radius_px', 8))
        candidates = [
            t for t in pool
            if t.confidence >= min_conf and t.image_dist <= radius_px
        ]
        self.last_in_zone_count = len(candidates)
        if not candidates:
            self.last_block_reason = 'outside_zone'
            self.reset()
            return

        delay_ms = max(
            0,
            int(_cfg_int(config, 'ai_trigger_delay_ms', 30) * self._rng.uniform(0.8, 1.2)),
        )
        cooldown_ms = max(
            0,
            int(_cfg_int(config, 'ai_trigger_cooldown_ms', 120) * self._rng.uniform(0.8, 1.2)),
        )

        now = _now_ms()
        if self._in_zone_since_ms <= 0.0:
            self._in_zone_since_ms = now

        linger_ok = (now - self._in_zone_since_ms) >= delay_ms
        cooldown_ok = (now - self._last_click_ms) >= cooldown_ms

        if not linger_ok:
            self.last_block_reason = 'delay'
            return
        if not cooldown_ok:
            self.last_block_reason = 'cooldown'
            return

        hold_ms = _cfg_int(config, 'ai_trigger_click_hold_ms', 20)
        makcu_manager.click('LMB', hold_ms=max(5, min(hold_ms, 40)))
        self._last_click_ms = now
        self.last_fire_at = time.time()
        self.last_block_reason = ''
        self._in_zone_since_ms = 0.0
