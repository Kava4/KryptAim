"""Weapon selection actions for local hotkey monitor."""

from __future__ import annotations

import logging

from Config.config_manager import load_config, save_config
from Recoil.recoil import reset_pattern_state
from Recoil.weapon_data import WeaponData

logger = logging.getLogger('AimSync.WeaponActions')


def get_available_weapons(game_id: str) -> list[str]:
    wd = WeaponData.get_game_data(game_id)
    weapons = [attr for attr in dir(wd) if not attr.startswith('_') and isinstance(getattr(wd, attr), list)]
    weapons.sort()
    return weapons


def set_active_weapon(config: dict, weapon_name: str, available_weapons: list[str]) -> bool:
    if weapon_name not in available_weapons:
        return False
    current_weapon = config.get('recoil_game_settings', {}).get('weapon')
    if current_weapon == weapon_name:
        return False
    config['recoil_game_settings']['weapon'] = weapon_name
    config['recoil_mode'] = 'CS2'
    save_config(config)
    reset_pattern_state()
    logger.info('Weapon selected: %s (CS2 mode)', weapon_name)
    return True


def cycle_weapon(config: dict | None = None) -> bool:
    config = config or load_config()
    game_id = config.get('active_game', 'cs2')
    available_weapons = get_available_weapons(game_id)
    if not available_weapons:
        return False
    current_wep = config.get('recoil_game_settings', {}).get('weapon', '')
    idx = available_weapons.index(current_wep) if current_wep in available_weapons else -1
    next_wep = available_weapons[(idx + 1) % len(available_weapons)]
    config['recoil_game_settings']['weapon'] = next_wep
    config['recoil_mode'] = 'CS2'
    save_config(config)
    reset_pattern_state()
    logger.info('Weapon cycled: %s -> %s (CS2 mode)', current_wep, next_wep)
    return True
