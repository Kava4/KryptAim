"""Detection region on the gaming PC screen."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DetectionRegion:
    left: int
    top: int
    width: int
    height: int

    @property
    def center_x(self) -> float:
        return self.left + self.width / 2.0

    @property
    def center_y(self) -> float:
        return self.top + self.height / 2.0
