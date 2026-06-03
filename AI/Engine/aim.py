"""Aim assist mouse movement (linear path, phase 1)."""

from __future__ import annotations

import random

from AI.Engine.settings import AiSettings
from AI.Engine.target import Prediction


class AimController:
    def __init__(self, settings: AiSettings, screen_width: int, screen_height: int) -> None:
        self._settings = settings
        self._screen_width = screen_width
        self._screen_height = screen_height
        self._rng = random.Random()

    def compute_move(self, target: Prediction) -> tuple[int, int]:
        half_w = self._screen_width // 2
        half_h = self._screen_height // 2

        left, top, width, height = target.detection_box
        aim_x = target.screen_center_x
        aim_y = target.screen_center_y

        x_offset = float(self._settings.sliders['X Offset (Left/Right)'])
        y_offset = float(self._settings.sliders['Y Offset (Up/Down)'])

        if self._settings.toggles['X Axis Percentage Adjustment']:
            x_pct = float(self._settings.sliders['X Offset (%)'])
            aim_x = left + width * (x_pct / 100.0)
        else:
            aim_x += x_offset

        if self._settings.toggles['Y Axis Percentage Adjustment']:
            y_pct = float(self._settings.sliders['Y Offset (%)'])
            aim_y = top + height - height * (y_pct / 100.0) + y_offset
        else:
            align = self._settings.dropdowns.get('Aiming Boundaries Alignment', 'Center')
            if align == 'Top':
                aim_y = top + y_offset
            elif align == 'Bottom':
                aim_y = top + height + y_offset
            else:
                aim_y = top + height / 2.0 + y_offset

        target_x = int(aim_x) - half_w
        target_y = int(aim_y) - half_h

        sensitivity = float(self._settings.sliders['Mouse Sensitivity (+/-)'])
        factor = max(0.0, min(1.0, 1.0 - sensitivity))

        move_x = int(target_x * factor)
        move_y = int(target_y * factor)

        jitter = int(self._settings.sliders['Mouse Jitter'])
        if jitter > 0:
            move_x += self._rng.randint(-jitter, jitter)
            move_y += self._rng.randint(-jitter, jitter)

        aspect = self._screen_width / max(1, self._screen_height)
        move_y = int(move_y / aspect)

        move_x = max(-150, min(150, move_x))
        move_y = max(-150, min(150, move_y))
        return move_x, move_y
