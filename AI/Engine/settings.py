"""Aimmy-compatible .cfg keys and runtime settings."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from Config.config_manager import get_ai_configs_dir

DEFAULT_TOGGLES: dict[str, bool] = {
    'Aim Assist': False,
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
    'FOV Size': 640.0,
    'Dynamic FOV Size': 200.0,
    'Mouse Sensitivity (+/-)': 0.80,
    'Mouse Jitter': 4.0,
    'Sticky Aim Threshold': 50.0,
    'Y Offset (Up/Down)': 0.0,
    'Y Offset (%)': 50.0,
    'X Offset (Left/Right)': 0.0,
    'X Offset (%)': 50.0,
    'Auto Trigger Delay': 0.1,
    'AI Minimum Confidence': 45.0,
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

AIMMY_KEYBIND_ALIASES = {
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
        for key, value in data.items():
            if key in self.toggles:
                self.toggles[key] = bool(value)
            elif key in self.sliders:
                self.sliders[key] = float(value)
            elif key in self.dropdowns:
                self.dropdowns[key] = str(value)

    def save_cfg(self, filename: str) -> None:
        path = get_ai_configs_dir() / filename
        merged: dict[str, Any] = {}
        merged.update(self.sliders)
        merged.update({k: v for k, v in self.toggles.items()})
        merged.update(self.dropdowns)
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
        for key, value in data.items():
            if key in self.toggles:
                self.toggles[key] = bool(value)
            elif key in self.sliders:
                self.sliders[key] = float(value)
            elif key in self.dropdowns:
                self.dropdowns[key] = str(value)

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

    def normalize_aimmy_key(self, key: str) -> str:
        return AIMMY_KEYBIND_ALIASES.get(key, key)
