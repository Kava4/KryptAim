"""Lead compensation for moving targets (trigger-only, no aim move)."""

from __future__ import annotations

import math
import time

from app.ai.types import Prediction


class TargetTracker:
    """Track closest-to-crosshair target velocity and extrapolate for trigger zone."""

    def __init__(self, *, match_px: float = 100.0) -> None:
        self._match_px = match_px
        self._cx = 0.0
        self._cy = 0.0
        self._vx = 0.0
        self._vy = 0.0
        self._last_t = 0.0
        self._active = False

    def reset(self) -> None:
        self._active = False
        self._vx = 0.0
        self._vy = 0.0

    def apply(
        self,
        targets: list[Prediction],
        *,
        image_size: int,
        lookahead_ms: float,
        inference_ms: float = 0.0,
    ) -> list[Prediction]:
        if not targets or lookahead_ms <= 0:
            if not targets:
                self.reset()
            return list(targets)

        best = min(targets, key=lambda t: t.image_dist)
        now = time.perf_counter()
        if self._active:
            dt = max(now - self._last_t, 0.001)
            dx = best.screen_center_x - self._cx
            dy = best.screen_center_y - self._cy
            jump = math.hypot(dx, dy)
            if jump > self._match_px:
                self._vx = 0.0
                self._vy = 0.0
            else:
                self._vx = dx / dt
                self._vy = dy / dt

        self._cx = best.screen_center_x
        self._cy = best.screen_center_y
        self._last_t = now
        self._active = True

        center = image_size / 2.0
        lead_s = (lookahead_ms + max(inference_ms, 0.0)) / 1000.0
        px = self._cx + self._vx * lead_s
        py = self._cy + self._vy * lead_s
        pred_dist = math.hypot(px - center, py - center)

        predicted = Prediction(
            confidence=best.confidence,
            image_dist=pred_dist,
            screen_center_x=px,
            screen_center_y=py,
        )
        rest = [t for t in targets if t is not best]
        return [predicted, *rest]
