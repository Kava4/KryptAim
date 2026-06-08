"""AimSync AI full profiles (setup + active aim .cfg reference)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from Config.config_manager import get_base_dir, load_config, save_config

PROFILE_SUFFIX = '.aiprofile.json'

AI_PROFILE_KEYS = (
    'ai_inference_backend',
    'ai_cuda_device_id',
    'ai_capture_mode',
    'ai_ndi_source',
    'ai_main_pc_width',
    'ai_main_pc_height',
    'ai_player_class',
    'ai_head_class',
    'ai_player_y_offset',
    'ai_region_size',
    'ai_always_on_aim',
    'ai_trigger_always_on',
    'ai_trigger_keybind',
    'ai_dynamic_fov_keybind',
    'ai_button_mask',
    'ai_mask_aim_button',
    'ai_mask_trigger_button',
    'ai_aim_humanization',
    'ai_detection_conf',
    'ai_imgsz',
    'ai_max_detect',
    'ai_aim_mode',
    'ai_in_game_sens',
    'ai_active_model',
    'ai_active_config',
    'ai_engine_enabled',
    'ai_trigger_radius_px',
    'ai_trigger_delay_ms',
    'ai_trigger_cooldown_ms',
    'ai_trigger_min_conf',
    'ai_trigger_linger_ms',
    'ai_normal_x_speed',
    'ai_normal_y_speed',
    'ai_bezier_segments',
    'ai_bezier_ctrl_x',
    'ai_bezier_ctrl_y',
    'ai_silent_segments',
    'ai_silent_ctrl_x',
    'ai_silent_ctrl_y',
    'ai_smooth_segments',
    'ai_smooth_gravity',
    'ai_smooth_wind',
    'ai_debug_preview',
    'ai_debug_cv2_window',
)


def get_profiles_dir() -> Path:
    path = get_base_dir() / 'bin' / 'profiles'
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_profiles() -> list[str]:
    return sorted(p.name for p in get_profiles_dir().glob(f'*{PROFILE_SUFFIX}'))


def export_profile_payload() -> dict[str, Any]:
    config = load_config()
    return {key: config.get(key) for key in AI_PROFILE_KEYS if key in config}


def save_profile(name: str) -> Path:
    stem = Path(name).stem
    if not stem:
        raise ValueError('Profile name is required.')
    path = get_profiles_dir() / f'{stem}{PROFILE_SUFFIX}'
    path.write_text(json.dumps(export_profile_payload(), indent=2), encoding='utf-8')
    return path


def load_profile(name: str) -> dict[str, Any]:
    path = get_profiles_dir() / name
    if not path.is_file() and not name.endswith(PROFILE_SUFFIX):
        path = get_profiles_dir() / f'{name}{PROFILE_SUFFIX}'
    if not path.is_file():
        raise FileNotFoundError(f'Profile not found: {name}')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('Profile file must be a JSON object.')
    return data


def apply_profile(name: str) -> dict[str, Any]:
    data = load_profile(name)
    config = load_config()
    for key in AI_PROFILE_KEYS:
        if key in data:
            config[key] = data[key]
    save_config(config)
    return config
