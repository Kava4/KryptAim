import copy
import json
import logging
import os
import sys
import threading
from pathlib import Path

from Config.app_identity import get_app_storage_dirname, is_beta_channel

logger = logging.getLogger('AimSync.Config')
_config_lock = threading.RLock()


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

BETA_DEFAULTS = {
    'ai_engine_enabled': False,
    'ai_active_model': '',
    'ai_active_config': 'Default.cfg',
    'ai_phase': 1,
    'ai_aim_keybind': 'rmb',
    'ai_second_aim_keybind': 'alt',
    'ai_engine_toggle_hotkey': 'None',
}

SAVED_PATTERNS_DIR = get_base_dir() / 'saved_patterns'
os.makedirs(SAVED_PATTERNS_DIR, exist_ok=True)


def get_bin_dir() -> Path:
    return get_base_dir() / 'bin'


def get_models_dir() -> Path:
    path = get_bin_dir() / 'models'
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_ai_configs_dir() -> Path:
    path = get_bin_dir() / 'configs'
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_ai_bin_dirs() -> None:
    for name in ('models', 'configs', 'images', 'labels'):
        (get_bin_dir() / name).mkdir(parents=True, exist_ok=True)


def _merge_defaults(data: dict) -> dict:
    for key, value in DEFAULTS.items():
        if key not in data:
            data[key] = copy.deepcopy(value) if isinstance(value, dict) else value
        elif isinstance(value, dict):
            for subkey, subvalue in value.items():
                if subkey not in data[key]:
                    data[key][subkey] = subvalue
    if is_beta_channel():
        for key, value in BETA_DEFAULTS.items():
            if key not in data:
                data[key] = copy.deepcopy(value) if isinstance(value, dict) else value
    return data


def _strip_beta_keys_for_save(config: dict) -> dict:
    if is_beta_channel():
        return config
    return {k: v for k, v in config.items() if k not in BETA_DEFAULTS}


def _default_config() -> dict:
    base = copy.deepcopy(DEFAULTS)
    if is_beta_channel():
        base.update(copy.deepcopy(BETA_DEFAULTS))
    return base


def _normalize_loaded_config(data: dict) -> dict:
    data = _merge_defaults(data)
    if not data.get('global_toggle_hotkey'):
        data['global_toggle_hotkey'] = data.get('recoil_keybind', DEFAULTS['global_toggle_hotkey'])
    if not data.get('weapon_cycle_hotkey'):
        data['weapon_cycle_hotkey'] = data.get('recoil_cycle_keybind', DEFAULTS['weapon_cycle_hotkey'])
    if not isinstance(data.get('weapon_direct_binds'), dict):
        data['weapon_direct_binds'] = copy.deepcopy(DEFAULTS['weapon_direct_binds'])
    return data


def _read_config_file() -> dict:
    if not CONFIG_FILE.is_file():
        return _default_config()

    raw = CONFIG_FILE.read_text(encoding='utf-8').strip()
    if not raw:
        raise json.JSONDecodeError('Config file is empty.', raw, 0)

    data = json.loads(raw)
    if not isinstance(data, dict):
        raise json.JSONDecodeError('Config root must be an object.', raw, 0)
    return _normalize_loaded_config(data)


def _recover_config_from_backup() -> dict | None:
    backup = CONFIG_FILE.with_suffix('.json.bak')
    if not backup.is_file():
        return None
    try:
        raw = backup.read_text(encoding='utf-8').strip()
        if not raw:
            return None
        data = json.loads(raw)
        if isinstance(data, dict):
            return _normalize_loaded_config(data)
    except (OSError, json.JSONDecodeError):
        return None
    return None


def load_config():
    with _config_lock:
        try:
            return _read_config_file()
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning('Config load failed (%s); attempting recovery.', exc)
            recovered = _recover_config_from_backup()
            if recovered is not None:
                logger.warning('Restored config from backup.')
                _write_config_file(recovered)
                return copy.deepcopy(recovered)

            logger.warning('Using default config after load failure.')
            defaults = _default_config()
            _write_config_file(defaults)
            return copy.deepcopy(defaults)


def _write_config_file(config: dict) -> None:
    os.makedirs(get_base_dir(), exist_ok=True)
    payload = _strip_beta_keys_for_save(config)
    tmp_path = CONFIG_FILE.with_suffix('.json.tmp')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    if CONFIG_FILE.is_file():
        backup = CONFIG_FILE.with_suffix('.json.bak')
        try:
            os.replace(CONFIG_FILE, backup)
        except OSError:
            pass
    os.replace(tmp_path, CONFIG_FILE)


def save_config(config):
    with _config_lock:
        _write_config_file(config)


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