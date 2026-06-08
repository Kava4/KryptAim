"""WindMouse human-like path generation (ported from vendor reference)."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class SmoothParams:
    gravity: float = 9.0
    wind: float = 3.0
    min_delay: float = 0.0
    max_delay: float = 0.002
    max_step: float = 40.0
    min_step: float = 2.0
    max_step_ratio: float = 0.2
    target_area_ratio: float = 0.06


def wind_mouse_path(
    dest_x: float,
    dest_y: float,
    *,
    params: SmoothParams | None = None,
    max_steps: int = 80,
    max_time_s: float = 0.35,
) -> list[tuple[int, int, float]]:
    """Return list of (dx, dy, delay_seconds) from origin to destination."""
    p = params or SmoothParams()
    current_x, current_y = 0.0, 0.0
    velocity_x = velocity_y = wind_x = wind_y = 0.0
    path: list[tuple[int, int, float]] = []
    carry_x = carry_y = 0.0
    total_time = 0.0
    distance = math.hypot(dest_x, dest_y)
    if distance < 2:
        return []

    target_area = max(2.0, distance * p.target_area_ratio)
    max_step = max(p.min_step, min(distance * p.max_step_ratio, p.max_step))

    while len(path) < max_steps and total_time < max_time_s:
        dist = math.hypot(dest_x - current_x, dest_y - current_y)
        if dist < target_area:
            break

        wind_x = wind_x / math.sqrt(3) + (random.random() - 0.5) * p.wind * 2
        wind_y = wind_y / math.sqrt(3) + (random.random() - 0.5) * p.wind * 2

        if dist > 1:
            gravity_x = p.gravity * (dest_x - current_x) / dist
            gravity_y = p.gravity * (dest_y - current_y) / dist
        else:
            gravity_x = gravity_y = 0.0

        velocity_x = (velocity_x + wind_x + gravity_x) * 0.995
        velocity_y = (velocity_y + wind_y + gravity_y) * 0.995

        step_size = math.hypot(velocity_x, velocity_y)
        if step_size > max_step:
            scale = max_step / step_size
            velocity_x *= scale
            velocity_y *= scale

        next_x = current_x + velocity_x
        next_y = current_y + velocity_y
        delay = random.uniform(p.min_delay, p.max_delay)

        carry_x += next_x - current_x
        carry_y += next_y - current_y
        out_dx = int(round(carry_x))
        out_dy = int(round(carry_y))
        carry_x -= out_dx
        carry_y -= out_dy

        if out_dx or out_dy:
            path.append((out_dx, out_dy, delay))

        current_x, current_y = next_x, next_y
        total_time += delay

    return path


def smooth_params_from_config(config: dict) -> SmoothParams:
    humanize = int(config.get('ai_aim_humanization', 0) or 0)
    wind = float(config.get('ai_smooth_wind', 3.0))
    if humanize > 0:
        wind += humanize * 0.15
    return SmoothParams(
        gravity=float(config.get('ai_smooth_gravity', 9.0)),
        wind=wind,
        min_delay=float(config.get('ai_smooth_min_delay', 0.0)),
        max_delay=float(config.get('ai_smooth_max_delay', 0.002)),
        max_step=float(config.get('ai_smooth_max_step', 40.0)),
        min_step=float(config.get('ai_smooth_min_step', 2.0)),
        max_step_ratio=float(config.get('ai_smooth_max_step_ratio', 0.2)),
        target_area_ratio=float(config.get('ai_smooth_target_area_ratio', 0.06)),
    )
