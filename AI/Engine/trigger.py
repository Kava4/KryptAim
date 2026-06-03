"""Auto trigger click logic (Aimmy-compatible)."""

from __future__ import annotations

import time

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

    def reset_spray(self) -> None:
        makcu_manager.reset_spray()

    def run_trigger(self, target: Prediction | None, aim_active: bool) -> None:
        if not self._settings.toggles['Auto Trigger'] or not aim_active:
            self.reset_spray()
            return

        if self._settings.toggles['Spray Mode']:
            if self._settings.toggles['Cursor Check'] and target is not None:
                mx, my = self._capture.cursor_position()
                left, top, w, h = target.detection_box
                if not (left <= mx <= left + w and top <= my <= top + h):
                    self.reset_spray()
                    return
            makcu_manager.hold_left()
            return

        if self._settings.toggles['Cursor Check'] and target is not None:
            mx, my = self._capture.cursor_position()
            left, top, w, h = target.detection_box
            if not (left <= mx <= left + w and top <= my <= top + h):
                return

        delay = float(self._settings.sliders['Auto Trigger Delay'])
        now = time.time()
        if self._last_click and (now - self._last_click) < delay:
            return
        makcu_manager.click('LMB', hold_ms=self._click_hold_ms)
        self._last_click = now
