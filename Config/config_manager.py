import copy
import json
import logging
import os
import sys
import threading
from pathlib import Path

from Config.app_identity import resolve_app_data_dir

logger = logging.getLogger('AimSync.Config')
_config_lock = threading.RLock()


def get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return resolve_app_data_dir()
    root = Path(__file__).resolve().parent.parent
    data_dir = root / '.aimsync-data'
    legacy_dir = root / '.beta-data'
    if legacy_dir.is_dir() and not data_dir.exists():
        return legacy_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


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
    'mouse_input_method': 'makcu',
    'ghub_dll_path': '',
    'arduino_port': 'COM0',
    'arduino_baudrate': 115200,
    'arduino_enable_keys': False,
    'rp2350_port': 'COM0',
    'rp2350_baudrate': 115200,
    'kmbox_net_ip': '10.42.42.42',
    'kmbox_net_port': '1984',
    'kmbox_net_uuid': 'DEADC0DE',
    'kmbox_a_pidvid': '',
    'razer_dll_path': '',
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
        'weapon': 'ak47',
        'sensitivity': 1.0,
        'recoil_loop': False,
        'timing_scale': 1.0,
    }
}

AI_DEFAULTS = {
    'ai_engine_enabled': False,
    'ai_active_model': '',
    'ai_active_config': 'Default.cfg',
    'ai_phase': 2,
    'ai_aim_keybind': 'rmb',
    'ai_second_aim_keybind': 'alt',
    'ai_engine_toggle_hotkey': 'None',
    'ai_inference_backend': 'cuda_ultralytics',
    'ai_cuda_device_id': 0,
    'ai_capture_mode': 'ndi',
    'ai_ndi_source': '',
    'ai_main_pc_width': 1920,
    'ai_main_pc_height': 1080,
    'ai_player_class': '',
    'ai_head_class': '',
    'ai_class_filter_mode': 'target_label',
    'ai_player_y_offset': 5,
    'ai_region_size': 200,
    'ai_always_on_aim': False,
    'ai_trigger_always_on': False,
    'ai_trigger_keybind': 'None',
    'ai_dynamic_fov_keybind': 'None',
    'ai_button_mask': False,
    'ai_mask_aim_button': 'RMB',
    'ai_mask_trigger_button': 'RMB',
    'ai_aim_humanization': 0,
    'ai_detection_conf': 0.25,
    'ai_imgsz': 640,
    'ai_max_detect': 50,
    'ai_aim_mode': 'normal',
    'ai_in_game_sens': 1.3,
    'ai_trigger_radius_px': 20,
    'ai_trigger_delay_ms': 30,
    'ai_trigger_cooldown_ms': 120,
    'ai_trigger_min_conf': 0.35,
    'ai_trigger_linger_ms': 30,
    'ai_normal_x_speed': 0.5,
    'ai_normal_y_speed': 0.5,
    'ai_bezier_segments': 8,
    'ai_bezier_ctrl_x': 16,
    'ai_bezier_ctrl_y': 16,
    'ai_silent_segments': 7,
    'ai_silent_ctrl_x': 18,
    'ai_silent_ctrl_y': 18,
    'ai_smooth_segments': 6,
    'ai_smooth_gravity': 9.0,
    'ai_smooth_wind': 3.0,
    'ai_smooth_min_delay': 0.0,
    'ai_smooth_max_delay': 0.002,
    'ai_smooth_max_step': 40.0,
    'ai_smooth_min_step': 2.0,
    'ai_smooth_max_step_ratio': 0.2,
    'ai_smooth_target_area_ratio': 0.06,
    'ai_debug_preview': True,
    'ai_debug_cv2_window': False,
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
    for key, value in AI_DEFAULTS.items():
        if key not in data:
            data[key] = copy.deepcopy(value) if isinstance(value, dict) else value
    return data


def _default_config() -> dict:
    base = copy.deepcopy(DEFAULTS)
    base.update(copy.deepcopy(AI_DEFAULTS))
    return base


def _normalize_loaded_config(data: dict) -> dict:
    data = _merge_defaults(data)
    if not data.get('global_toggle_hotkey'):
        data['global_toggle_hotkey'] = data.get('recoil_keybind', DEFAULTS['global_toggle_hotkey'])
    if not data.get('weapon_cycle_hotkey'):
        data['weapon_cycle_hotkey'] = data.get('recoil_cycle_keybind', DEFAULTS['weapon_cycle_hotkey'])
    if not isinstance(data.get('weapon_direct_binds'), dict):
        data['weapon_direct_binds'] = copy.deepcopy(DEFAULTS['weapon_direct_binds'])
    game_settings = data.get('recoil_game_settings') or {}
    weapon = game_settings.get('weapon')
    if weapon in {None, '', 'assault_rifle'}:
        game_settings['weapon'] = 'ak47'
        data['recoil_game_settings'] = game_settings
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


def _persist_config_migration(config: dict) -> None:
    """Reserved for one-time on-disk migrations (no-op today)."""
    del config


def load_config():
    with _config_lock:
        try:
            config = _read_config_file()
            _persist_config_migration(config)
            return config
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning('Config load failed (%s); attempting recovery.', exc)
            recovered = _recover_config_from_backup()
            if recovered is not None:
                logger.warning('Restored config from backup.')
                _persist_config_migration(recovered)
                _write_config_file(recovered)
                return copy.deepcopy(recovered)

            logger.warning('Using default config after load failure.')
            defaults = _default_config()
            _write_config_file(defaults)
            return copy.deepcopy(defaults)


def _write_config_file(config: dict) -> None:
    os.makedirs(get_base_dir(), exist_ok=True)
    payload = config
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