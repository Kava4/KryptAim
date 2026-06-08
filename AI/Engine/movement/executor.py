"""Execute aim movement via Makcu (normal, bezier, silent, smooth, exponential)."""

from __future__ import annotations

import logging
import math
import queue
import time
from typing import TYPE_CHECKING

from AI.Engine.movement.windmouse import smooth_params_from_config, wind_mouse_path
from Input.methods import use_alt_input
from Input.router import input_router
from Makcu.makcu_manager import makcu_manager

if TYPE_CHECKING:
    from AI.Engine.settings import AiSettings

logger = logging.getLogger('AimSync.AI.Movement')

_PATH_TO_MODE = {
    'Linear': 'normal',
    'Cubic Bezier': 'bezier',
    'Exponential': 'exponential',
    'Adaptive': 'smooth',
}


def scale_in_game_sensitivity(dx: int, dy: int, config: dict) -> tuple[int, int]:
    sens = float(config.get('ai_in_game_sens', 1.0) or 1.0)
    if sens <= 0:
        return dx, dy
    factor = 1.07437623 * math.pow(sens, -0.9936827126)
    return int(dx * factor), int(dy * factor)


class MovementExecutor:
    def __init__(self, smooth_queue: queue.Queue | None = None) -> None:
        self._smooth_queue = smooth_queue

    @staticmethod
    def resolve_mode(config: dict, settings: 'AiSettings') -> str:
        cfg_mode = (config.get('ai_aim_mode') or '').strip().lower()
        if cfg_mode in {'normal', 'bezier', 'silent', 'smooth', 'exponential'}:
            return cfg_mode
        path = settings.dropdowns.get('Movement Path', 'Linear')
        return _PATH_TO_MODE.get(path, 'normal')

    def apply(self, dx: int, dy: int, config: dict, settings: 'AiSettings') -> None:
        if dx == 0 and dy == 0:
            return

        dx, dy = scale_in_game_sensitivity(dx, dy, config)
        if dx == 0 and dy == 0:
            return

        mode = self.resolve_mode(config, settings)
        speed_x = float(config.get('ai_normal_x_speed', 0.5))
        speed_y = float(config.get('ai_normal_y_speed', 0.5))

        if use_alt_input(config):
            self._apply_alt(dx, dy, config, settings, mode, speed_x, speed_y)
            return

        if mode == 'normal':
            makcu_manager.move(int(dx * speed_x), int(dy * speed_y))
            return

        if mode == 'bezier':
            makcu_manager.move_bezier(
                dx,
                dy,
                segments=int(config.get('ai_bezier_segments', 8)),
                ctrl_x=int(config.get('ai_bezier_ctrl_x', 16)),
                ctrl_y=int(config.get('ai_bezier_ctrl_y', 16)),
            )
            return

        if mode == 'silent':
            makcu_manager.move_bezier(
                dx,
                dy,
                segments=int(config.get('ai_silent_segments', 7)),
                ctrl_x=int(config.get('ai_silent_ctrl_x', 18)),
                ctrl_y=int(config.get('ai_silent_ctrl_y', 18)),
            )
            return

        if mode == 'exponential':
            segments = int(config.get('ai_smooth_segments', 6))
            makcu_manager.move_smooth(dx, dy, segments=max(2, segments))
            return

        if mode == 'smooth':
            path = wind_mouse_path(float(dx), float(dy), params=smooth_params_from_config(config))
            if not path:
                makcu_manager.move(dx, dy)
                return
            if self._smooth_queue is not None:
                queued = 0
                for step_dx, step_dy, delay in path:
                    try:
                        self._smooth_queue.put_nowait((step_dx, step_dy, delay))
                        queued += 1
                    except queue.Full:
                        break
                if queued:
                    return
            for step_dx, step_dy, _delay in path[:12]:
                makcu_manager.move(step_dx, step_dy)
            return

        makcu_manager.move(dx, dy)

    def _apply_alt(
        self,
        dx: int,
        dy: int,
        config: dict,
        settings: 'AiSettings',
        mode: str,
        speed_x: float,
        speed_y: float,
    ) -> None:
        if mode == 'normal':
            input_router.move(int(dx * speed_x), int(dy * speed_y))
            return
        if mode in {'bezier', 'silent', 'exponential'}:
            segments = int(config.get('ai_bezier_segments', 8) if mode == 'bezier' else config.get('ai_silent_segments', 7))
            if mode == 'exponential':
                segments = int(config.get('ai_smooth_segments', 6))
            input_router.move_smooth_steps(dx, dy, segments=max(2, segments))
            return
        if mode == 'smooth':
            path = wind_mouse_path(float(dx), float(dy), params=smooth_params_from_config(config))
            if not path:
                input_router.move(dx, dy)
                return
            if self._smooth_queue is not None:
                queued = 0
                for step_dx, step_dy, delay in path:
                    try:
                        self._smooth_queue.put_nowait((step_dx, step_dy, delay))
                        queued += 1
                    except queue.Full:
                        break
                if queued:
                    return
            for step_dx, step_dy, _delay in path[:12]:
                input_router.move(step_dx, step_dy)
            return
        input_router.move(dx, dy)


def smooth_movement_loop(stop_event, move_queue: queue.Queue) -> None:
    """Background thread for windmouse steps with timing."""
    from Config.config_manager import load_config

    while not stop_event.is_set():
        try:
            dx, dy, delay = move_queue.get(timeout=0.05)
        except queue.Empty:
            continue
        try:
            if use_alt_input(load_config()):
                input_router.move(dx, dy)
            else:
                makcu_manager.move(dx, dy)
            if delay > 0:
                time.sleep(delay)
        except Exception as exc:
            logger.debug('Smooth move failed: %s', exc)
