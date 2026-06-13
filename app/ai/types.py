"""AI detection types — minimal until YOLO wiring lands."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Prediction:
    confidence: float
    image_dist: float
    screen_center_x: float = 0.0
    screen_center_y: float = 0.0
    is_head: bool = False
