from dataclasses import dataclass
from typing import List, Sequence


@dataclass
class SprayPoint:
    x: float
    y: float


def normalize_points(points: Sequence[dict]) -> List[SprayPoint]:
    normalized: List[SprayPoint] = []
    for point in points:
        try:
            x = float(point.get("x"))
            y = float(point.get("y"))
        except (TypeError, ValueError, AttributeError):
            continue
        normalized.append(SprayPoint(x=x, y=y))
    return normalized


def validate_points(points: Sequence[SprayPoint], minimum: int = 2) -> None:
    if len(points) < minimum:
        raise ValueError(f"At least {minimum} points are required.")
