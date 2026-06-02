import copy
import json
import os
import sys
from pathlib import Path

from Config.app_identity import get_app_storage_dirname


def get_base_dir() -> Path:
    # Persistent storage: Use the executable's directory instead of the temporary extraction folder
    if getattr(sys, 'frozen', False):
        # Move persistent data to AppData/Roaming/<channel specific app dir> to keep EXE folders clean
        app_data = Path(os.environ.get('APPDATA', Path.home())) / get_app_storage_dirname()
        app_data.mkdir(parents=True, exist_ok=True)
        return app_data
    # Dev mode: Root directory
    channel = os.environ.get('AIMSYNC_CHANNEL', '').strip().lower()
    if channel == 'beta':
        beta_dir = Path(__file__).resolve().parent.parent / '.beta-data'
        beta_dir.mkdir(parents=True, exist_ok=True)
        return beta_dir
    return Path(__file__).resolve().parent.parent


CONFIG_FILE = get_base_dir() / 'config.json'

DEFAULTS = {
    'recoil_enabled': False,
    'recoil_keybind': 'M4',
    'global_toggle_hotkey': 'M4',
    'recoil_mode': 'simple',
    'recoil_require_rmb': False,
    'recoil_randomisation': False,
    'recoil_random_strength': 5.0,
    'recoil_cycle_keybind': 'None',
    'weapon_cycle_hotkey': 'None',
    'weapon_direct_binds': {},
    'recoil_x_control': 100,
    'recoil_safety_features_enabled': True,
    'recoil_y_control': 100,
    'recoil_speed_control': 100,
    'recoil_input_method': 'hardware',
    'recoil_return_crosshair': False,
    'shutdown_on_app_stop': False,
    'active_game': 'cs2',
    'license_key': '',
    'is_premium': False,
    'cloud_username': 'Anonymous',
    'ocr_enabled': False,
    'ocr_poll_ms': 250,
    'ocr_roi_cs2': {
        'x': 0,
        'y': 0,
        'width': 0,
        'height': 0,
    },
    'ocr_confidence_threshold': 0.7,
    'ocr_helper_ws_url': 'ws://0.0.0.0:8765/ws/ocr',
    'ocr_helper_token': '',
    'ocr_debug_log': False,
    'recoil_simple_settings': {
        'recoil_x': 0,
        'recoil_y': 0,
        'recoil_delay': 50
    },
    'recoil_advanced_settings': {
        'recoil_loop': False,
        'recoil_selected_pattern': [],
        'recoil_active_pattern_name': ''
    },
    'recoil_game_settings': {
        'weapon': 'assault_rifle',
        'sensitivity': 1.0,
        'recoil_loop': False
    }
}

SAVED_PATTERNS_DIR = get_base_dir() / 'saved_patterns'
os.makedirs(SAVED_PATTERNS_DIR, exist_ok=True)


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding='utf-8') as f:
            data = json.load(f)
        for key, value in DEFAULTS.items():
            if key not in data:
                data[key] = value
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if subkey not in data[key]:
                        data[key][subkey] = subvalue
        if not data.get('global_toggle_hotkey'):
            data['global_toggle_hotkey'] = data.get('recoil_keybind', DEFAULTS['global_toggle_hotkey'])
        if not data.get('weapon_cycle_hotkey'):
            data['weapon_cycle_hotkey'] = data.get('recoil_cycle_keybind', DEFAULTS['weapon_cycle_hotkey'])
        if not isinstance(data.get('weapon_direct_binds'), dict):
            data['weapon_direct_binds'] = copy.deepcopy(DEFAULTS['weapon_direct_binds'])
        return data
    return copy.deepcopy(DEFAULTS)


def save_config(config):
    os.makedirs(get_base_dir(), exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def get_pattern_names():
    os.makedirs(SAVED_PATTERNS_DIR, exist_ok=True)
    return sorted([f.replace('.json', '') for f in os.listdir(SAVED_PATTERNS_DIR) if f.endswith('.json')])


def load_pattern_file(name):
    path = SAVED_PATTERNS_DIR / f'{name}.json'
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def save_pattern_file(name, pattern):
    os.makedirs(SAVED_PATTERNS_DIR, exist_ok=True)
    path = SAVED_PATTERNS_DIR / f'{name}.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(pattern, f, indent=2)


def delete_pattern_file(name):
    path = SAVED_PATTERNS_DIR / f'{name}.json'
    if os.path.exists(path):
        os.remove(path)