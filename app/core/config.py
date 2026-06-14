"""App config — CS2 recoil."""

from __future__ import annotations

import copy
import json
import os
import threading
from pathlib import Path

from app.core.identity import APP_STORAGE_DIR, LEGACY_STORAGE_DIR

_io_lock = threading.Lock()
_last_good: dict | None = None

DEFAULTS: dict = {
    'recoil_enabled': False,
    'recoil_keybind': 'M4',
    'recoil_mode': 'CS2',
    'recoil_require_rmb': False,
    'recoil_return_crosshair': False,
    'recoil_randomisation': False,
    'recoil_random_strength': 5.0,
    'recoil_x_control': 100,
    'recoil_y_control': 100,
    'shutdown_on_app_stop': False,
    'cloud_username': 'Anonymous',
    'license_key': '',
    'is_premium': False,
    'mouse_input_method': 'makcu',
    'recoil_cs2_settings': {
        'cs2_weapon': 'assault_rifle',
        'cs2_sensitivity': 1.25,
    },
    'ai_enabled': False,
    'ai_assist_mode': 'trigger',
    'ai_aim_enabled': False,
    'ai_aim_always_on': False,
    'ai_aim_keybind': 'M4',
    'ai_aim_speed': 1.0,
    'ai_aim_max_px': 280,
    'ai_trigger_enabled': False,
    'ai_trigger_always_on': False,
    'ai_trigger_keybind': 'M4',
    'ai_trigger_radius_px': 8,
    'ai_trigger_delay_ms': 30,
    'ai_trigger_cooldown_ms': 120,
    'ai_trigger_min_conf': 0.35,
    'ai_trigger_click_hold_ms': 20,
    'ai_trigger_prediction_ms': 35,
    'ai_trigger_spray_block': True,
    'ai_capture_mode': 'ndi',
    'ai_ndi_source': '',
    'ai_main_pc_width': 1920,
    'ai_main_pc_height': 1080,
    'ai_region_size': 640,
    'ai_model_path': '',
    'ai_detection_conf': 0.25,
    'ai_player_class': '',
    'ai_head_class': '',
    'ai_my_team': '',
    'ai_aim_point': 'head',
}


def config_dir() -> Path:
    custom = os.environ.get('KRYPTAIM_CONFIG_DIR') or os.environ.get('KRYPTAIM_CONFIG_DIR')
    if custom:
        path = Path(custom)
        path.mkdir(parents=True, exist_ok=True)
        return path

    base = Path(os.environ.get('APPDATA', Path.home()))
    new_path = base / APP_STORAGE_DIR
    legacy_path = base / LEGACY_STORAGE_DIR
    if new_path.is_dir():
        return new_path
    if legacy_path.is_dir():
        return legacy_path
    new_path.mkdir(parents=True, exist_ok=True)
    return new_path


def config_path() -> Path:
    return config_dir() / 'config.json'


def _merge_defaults(data: dict) -> dict:
    out = copy.deepcopy(DEFAULTS)
    for key, value in data.items():
        if key not in out:
            out[key] = value
        elif isinstance(out[key], dict) and isinstance(value, dict):
            merged = copy.deepcopy(out[key])
            merged.update(value)
            out[key] = merged
        else:
            out[key] = value
    out['recoil_mode'] = 'CS2'
    weapon = out.get('recoil_cs2_settings', {}).get('cs2_weapon')
    if weapon == 'ak47':
        out['recoil_cs2_settings']['cs2_weapon'] = 'assault_rifle'
    _sync_assist_mode(out)
    return out


def _sync_assist_mode(config: dict) -> None:
    """Keep aim/trigger flags aligned with ai_assist_mode combo."""
    mode = str(config.get('ai_assist_mode', 'trigger') or 'trigger').lower()
    if mode == 'aim':
        config['ai_aim_enabled'] = True
        config['ai_trigger_enabled'] = False
        config['ai_trigger_prediction_ms'] = 0
    elif mode == 'trigger':
        config['ai_aim_enabled'] = False
        config['ai_trigger_enabled'] = True
    elif mode == 'both':
        config['ai_aim_enabled'] = True
        config['ai_trigger_enabled'] = True
    else:
        config['ai_assist_mode'] = 'trigger'
        config['ai_aim_enabled'] = False
        config['ai_trigger_enabled'] = True


def _read_json_file(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding='utf-8').strip()
        if not text:
            return None
        data = json.loads(text)
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def load_config() -> dict:
    global _last_good
    with _io_lock:
        path = config_path()
        for candidate in (path, path.with_suffix('.json.bak')):
            data = _read_json_file(candidate)
            if data is not None:
                merged = _merge_defaults(data)
                _last_good = copy.deepcopy(merged)
                return merged
        if _last_good is not None:
            return copy.deepcopy(_last_good)
        return copy.deepcopy(DEFAULTS)


def save_config(config: dict) -> None:
    global _last_good
    with _io_lock:
        payload = _merge_defaults(config)
        path = config_path()
        tmp = path.with_suffix('.json.tmp')
        body = json.dumps(payload, indent=2)
        tmp.write_text(body, encoding='utf-8')
        tmp.replace(path)
        bak = path.with_suffix('.json.bak')
        try:
            bak.write_text(body, encoding='utf-8')
        except OSError:
            pass
        _last_good = copy.deepcopy(payload)
