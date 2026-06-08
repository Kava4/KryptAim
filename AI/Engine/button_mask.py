"""Makcu button lock while aim/trigger is active (blocks physical click-through)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Makcu.makcu_manager import MakcuManager

logger = logging.getLogger('AimSync.AI.ButtonMask')

# 0=LMB … 4=M5 (matches Makcu MouseButton enum order).
BUTTON_NAME_TO_IDX: dict[str, int] = {
    'LMB': 0,
    'LEFT': 0,
    'RMB': 1,
    'RIGHT': 1,
    'MMB': 2,
    'MIDDLE': 2,
    'M4': 3,
    'MOUSE4': 3,
    'S4': 3,
    'M5': 4,
    'MOUSE5': 4,
    'S5': 4,
}


def button_name_to_idx(name: str) -> int | None:
    key = (name or '').strip().upper()
    if not key or key == 'NONE':
        return None
    return BUTTON_NAME_TO_IDX.get(key)


def mask_indices_from_config(config: dict) -> list[int]:
    """Buttons to lock while AI is actively aiming/triggering."""
    indices: list[int] = []
    for key in ('ai_mask_aim_button', 'ai_mask_trigger_button'):
        idx = button_name_to_idx(str(config.get(key, '') or ''))
        if idx is not None and idx not in indices:
            indices.append(idx)
    return indices


def mask_manager_tick(manager: 'MakcuManager', button_indices: list[int], running: bool) -> None:
    manager.apply_button_mask(button_indices, running)
