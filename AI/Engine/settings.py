"""AimSync AI profile storage (.cfg JSON) — alias keys via profile_sync."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from Config.config_manager import get_ai_configs_dir

DEFAULT_TOGGLES: dict[str, bool] = {
    'Aim Assist': False,
    'Dynamic FOV': False,
    'Sticky Aim': False,
    'Constant AI Tracking': False,
    'Predictions': False,
    'Auto Trigger': False,
    'Cursor Check': False,
    'Spray Mode': False,
    'X Axis Percentage Adjustment': False,
    'Y Axis Percentage Adjustment': False,
}

DEFAULT_SLIDERS: dict[str, float] = {
    'FOV Size': 200.0,
    'Dynamic FOV Size': 200.0,
    'Mouse Sensitivity (+/-)': 0.0,
    'Mouse Jitter': 0.0,
    'Sticky Aim Threshold': 50.0,
    'Y Offset (Up/Down)': 0.0,
    'Y Offset (%)': 50.0,
    'X Offset (Left/Right)': 0.0,
    'X Offset (%)': 50.0,
    'Auto Trigger Delay': 0.1,
    'AI Minimum Confidence': 20.0,
}

DEFAULT_DROPDOWNS: dict[str, str] = {
    'Prediction Method': 'Kalman Filter',
    'Detection Area Type': 'Closest to Center Screen',
    'Aiming Boundaries Alignment': 'Center',
    'Movement Path': 'Linear',
    'Target Class': 'Best Confidence',
    'Image Size': '640',
}

SLIDER_SPECS: dict[str, dict[str, float]] = {
    'FOV Size': {'min': 50, 'max': 640, 'step': 1},
    'Dynamic FOV Size': {'min': 50, 'max': 640, 'step': 1},
    'Mouse Sensitivity (+/-)': {'min': 0, 'max': 1, 'step': 0.01},
    'Mouse Jitter': {'min': 0, 'max': 20, 'step': 1},
    'Sticky Aim Threshold': {'min': 0, 'max': 100, 'step': 1},
    'Y Offset (Up/Down)': {'min': -100, 'max': 100, 'step': 1},
    'Y Offset (%)': {'min': 0, 'max': 100, 'step': 1},
    'X Offset (Left/Right)': {'min': -100, 'max': 100, 'step': 1},
    'X Offset (%)': {'min': 0, 'max': 100, 'step': 1},
    'Auto Trigger Delay': {'min': 0, 'max': 1, 'step': 0.01},
    'AI Minimum Confidence': {'min': 1, 'max': 100, 'step': 1},
}

DROPDOWN_OPTIONS: dict[str, list[str]] = {
    'Prediction Method': ['Kalman Filter', "Shall0e's Prediction", 'Linear'],
    'Detection Area Type': ['Closest to Center Screen', 'Closest to Mouse'],
    'Aiming Boundaries Alignment': ['Center', 'Top', 'Bottom'],
    'Movement Path': ['Linear', 'Cubic Bezier', 'Exponential', 'Adaptive'],
    'Target Class': ['Best Confidence'],
    'Image Size': ['320', '416', '640', '1280'],
}

TOGGLE_GROUPS: dict[str, list[str]] = {
    'Aim & tracking': [
        'Aim Assist',
        'Dynamic FOV',
        'Sticky Aim',
        'Constant AI Tracking',
        'Predictions',
        'Cursor Check',
    ],
    'Trigger': ['Auto Trigger', 'Spray Mode'],
    'Offset mode': ['X Axis Percentage Adjustment', 'Y Axis Percentage Adjustment'],
}

SLIDER_GROUPS: dict[str, list[str]] = {
    'Detection': ['FOV Size', 'Dynamic FOV Size', 'AI Minimum Confidence'],
    'Aim tuning': [
        'Mouse Sensitivity (+/-)',
        'Mouse Jitter',
        'Sticky Aim Threshold',
        'X Offset (Left/Right)',
        'Y Offset (Up/Down)',
        'X Offset (%)',
        'Y Offset (%)',
    ],
    'Trigger timing': ['Auto Trigger Delay'],
}

HOTKEY_ALIASES = {
    'Right': 'RMB',
    'Left': 'LMB',
    'Middle': 'MMB',
    'LMenu': 'alt',
    'RMenu': 'alt',
    'Delete': 'Delete',
    'OemPipe': 'OemPipe',
    'Oem6': 'Oem6',
    'D1': '1',
    'D2': '2',
}


# Default AI baseline — experimental tuning deviates from these values.
BASELINE_SLIDERS: dict[str, float] = {
    'Mouse Sensitivity (+/-)': 0.0,
    'Mouse Jitter': 0.0,
    'Y Offset (Up/Down)': 0.0,
    'X Offset (Left/Right)': 0.0,
    'X Offset (%)': 50.0,
    'Y Offset (%)': 50.0,
    'Sticky Aim Threshold': 50.0,
}

BASELINE_TOGGLES: dict[str, bool] = {
    'Sticky Aim': False,
    'Predictions': False,
    'Dynamic FOV': False,
    'X Axis Percentage Adjustment': False,
    'Y Axis Percentage Adjustment': False,
}

BASELINE_DROPDOWNS: dict[str, str] = {
    'Movement Path': 'Linear',
    'Prediction Method': 'Linear',
    'Aiming Boundaries Alignment': 'Center',
}


def is_experimental_slider(name: str, value: float) -> bool:
    baseline = BASELINE_SLIDERS.get(name)
    if baseline is None:
        return False
    try:
        return abs(float(value) - float(baseline)) > 1e-6
    except (TypeError, ValueError):
        return True


def is_experimental_toggle(name: str, enabled: bool) -> bool:
    baseline = BASELINE_TOGGLES.get(name)
    if baseline is None:
        return False
    return bool(enabled) != bool(baseline)


def is_experimental_dropdown(name: str, value: str) -> bool:
    baseline = BASELINE_DROPDOWNS.get(name)
    if baseline is None:
        return False
    return str(value or '').strip() != baseline


def apply_default_ai_profile(settings: 'AiSettings') -> None:
    """Default starter profile (direct aim — no extra smoothing/jitter layers)."""
    settings.toggles['Aim Assist'] = True
    settings.toggles['Auto Trigger'] = False
    settings.toggles['Constant AI Tracking'] = False
    settings.toggles['Sticky Aim'] = False
    settings.toggles['Predictions'] = False
    settings.toggles['Dynamic FOV'] = False
    settings.toggles['X Axis Percentage Adjustment'] = False
    settings.toggles['Y Axis Percentage Adjustment'] = False
    settings.sliders['AI Minimum Confidence'] = 20.0
    settings.sliders['FOV Size'] = 200.0
    settings.sliders['Mouse Sensitivity (+/-)'] = 0.0
    settings.sliders['Mouse Jitter'] = 0.0
    settings.sliders['Y Offset (Up/Down)'] = 0.0
    settings.sliders['X Offset (Left/Right)'] = 0.0
    settings.dropdowns['Detection Area Type'] = 'Closest to Center Screen'
    settings.dropdowns['Movement Path'] = 'Linear'
    settings.dropdowns['Prediction Method'] = 'Linear'
    settings.dropdowns['Aiming Boundaries Alignment'] = 'Center'
    settings.dropdowns['Image Size'] = '640'


def apply_starter_profile(settings: 'AiSettings') -> None:
    """Alias for quickstart / legacy callers."""
    apply_default_ai_profile(settings)


class AiSettings:
    def __init__(self) -> None:
        self.toggles: dict[str, bool] = copy.deepcopy(DEFAULT_TOGGLES)
        self.sliders: dict[str, float] = copy.deepcopy(DEFAULT_SLIDERS)
        self.dropdowns: dict[str, str] = copy.deepcopy(DEFAULT_DROPDOWNS)

    def load_cfg(self, filename: str) -> None:
        path = get_ai_configs_dir() / filename
        if not path.is_file():
            self.save_cfg(filename)
            return
        with open(path, encoding='utf-8') as handle:
            data = json.load(handle)
        from AI.Engine.profile_sync import import_profile_dict

        import_profile_dict(data, self)

    def save_cfg(self, filename: str, *, use_alias_keys: bool = True) -> None:
        path = get_ai_configs_dir() / filename
        if use_alias_keys:
            from AI.Engine.profile_sync import export_profile_dict

            merged = export_profile_dict(self)
        else:
            merged = self.export_cfg_dict()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as handle:
            json.dump(merged, handle, indent=2)

    def read_cfg_file(self, filename: str) -> dict[str, Any]:
        path = get_ai_configs_dir() / filename
        if not path.is_file():
            self.save_cfg(filename)
        with open(path, encoding='utf-8') as handle:
            return json.load(handle)

    def write_cfg_file(self, filename: str, data: dict[str, Any]) -> None:
        path = get_ai_configs_dir() / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as handle:
            json.dump(data, handle, indent=2)
        self.apply_cfg_dict(data)

    def apply_cfg_dict(self, data: dict[str, Any]) -> None:
        from AI.Engine.profile_sync import import_profile_dict

        import_profile_dict(data, self)

    def export_cfg_dict(self) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        merged.update(self.sliders)
        merged.update(self.toggles)
        merged.update(self.dropdowns)
        return merged

    def image_size(self) -> int:
        try:
            return int(float(self.dropdowns.get('Image Size', '640')))
        except (TypeError, ValueError):
            return 640

    def normalize_hotkey(self, key: str) -> str:
        return HOTKEY_ALIASES.get(key, key)
