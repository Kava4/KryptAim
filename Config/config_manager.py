import json
import os
import sys
from pathlib import Path


def get_base_dir() -> Path:
    # Persistent storage: Use the executable's directory instead of the temporary extraction folder
    if getattr(sys, 'frozen', False):
        # Move persistent data to AppData/Roaming/AimSync to keep the EXE folder clean
        app_data = Path(os.environ.get('APPDATA', Path.home())) / 'AimSync'
        app_data.mkdir(parents=True, exist_ok=True)
        return app_data
    # Dev mode: Root directory
    return Path(__file__).resolve().parent.parent


CONFIG_FILE = get_base_dir() / 'config.json'

DEFAULTS = {
    'recoil_enabled': False,
    'recoil_keybind': 'M4',
    'recoil_mode': 'simple',
    'recoil_require_rmb': False,
    'recoil_randomisation': False,
    'recoil_random_strength': 5.0,
    'recoil_cycle_keybind': 'None',
    'recoil_x_control': 100,
    'recoil_safety_features_enabled': True,
    'recoil_y_control': 100,
    'shutdown_on_app_stop': False,
    'active_game': 'cs2',
    'license_key': '',
    'is_premium': False,
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
        return data
    return DEFAULTS.copy()


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