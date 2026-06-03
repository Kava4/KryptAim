"""Optional prediction smoothing (phase 2 / beta)."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DetectionPoint:
    x: int
    y: int
    timestamp: datetime


class KalmanPredictor:
    """Lightweight 2D Kalman-style smoother for aim assist."""

    def __init__(self) -> None:
        self._position = (0.0, 0.0)
        self._velocity = (0.0, 0.0)
        self._initialized = False

    def update(self, x: int, y: int) -> tuple[int, int]:
        if not self._initialized:
            self._position = (float(x), float(y))
            self._initialized = True
            return x, y

        predicted_x = self._position[0] + self._velocity[0]
        predicted_y = self._position[1] + self._velocity[1]
        residual_x = x - predicted_x
        residual_y = y - predicted_y
        gain = 0.35
        self._position = (predicted_x + gain * residual_x, predicted_y + gain * residual_y)
        self._velocity = (
            0.6 * self._velocity[0] + 0.4 * (self._position[0] - predicted_x),
            0.6 * self._velocity[1] + 0.4 * (self._position[1] - predicted_y),
        )
        return int(self._position[0]), int(self._position[1])

    def reset(self) -> None:
        self._initialized = False
        self._position = (0.0, 0.0)
        self._velocity = (0.0, 0.0)


class ShalloePredictor:
    def __init__(self, window: int = 5) -> None:
        self._dx = deque(maxlen=window)
        self._dy = deque(maxlen=window)

    def predict(self, x: int, y: int, prev_x: int, prev_y: int) -> tuple[int, int]:
        self._dx.append(x - prev_x)
        self._dy.append(y - prev_y)
        if not self._dx:
            return x, y
        avg_dx = sum(self._dx) / len(self._dx)
        avg_dy = sum(self._dy) / len(self._dy)
        return int(x + avg_dx), int(y + avg_dy)
