"""Map profile .cfg / config.json fields to AimSync AI engine runtime keys."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from AI.Engine.settings import AiSettings

# Short keys in exported .cfg JSON → internal profile keys.
PROFILE_ALIAS_MAP: dict[str, str] = {
    'region_size': 'FOV Size',
    'dynamic_region_size': 'Dynamic FOV Size',
    'dynamic_fov': 'Dynamic FOV',
    'always_on_aim': 'Constant AI Tracking',
    'aim_assist': 'Aim Assist',
    'auto_trigger': 'Auto Trigger',
    'trigger_spray': 'Spray Mode',
    'cursor_check': 'Cursor Check',
    'sticky_aim': 'Sticky Aim',
    'predictions': 'Predictions',
    'mouse_sensitivity': 'Mouse Sensitivity (+/-)',
    'mouse_jitter': 'Mouse Jitter',
    'sticky_threshold': 'Sticky Aim Threshold',
    'y_offset': 'Y Offset (Up/Down)',
    'y_offset_pct': 'Y Offset (%)',
    'x_offset': 'X Offset (Left/Right)',
    'x_offset_pct': 'X Offset (%)',
    'trigger_delay_s': 'Auto Trigger Delay',
    'min_confidence_pct': 'AI Minimum Confidence',
    'detection_area': 'Detection Area Type',
    'aim_alignment': 'Aiming Boundaries Alignment',
    'movement_path': 'Movement Path',
    'prediction_method': 'Prediction Method',
}

PROFILE_ALIAS_REVERSE: dict[str, str] = {v: k for k, v in PROFILE_ALIAS_MAP.items()}


def apply_config_globals(settings: 'AiSettings', config: dict[str, Any]) -> None:
    """Push global AI fields from config.json into the active profile runtime."""
    if config.get('ai_always_on_aim') is not None:
        settings.toggles['Constant AI Tracking'] = bool(config.get('ai_always_on_aim'))
    if config.get('ai_aim_assist') is not None:
        settings.toggles['Aim Assist'] = bool(config.get('ai_aim_assist'))
    if config.get('ai_trigger_always_on'):
        settings.toggles['Auto Trigger'] = True
    if config.get('ai_trigger_enabled') is not None:
        settings.toggles['Auto Trigger'] = bool(config.get('ai_trigger_enabled'))
    region = config.get('ai_region_size')
    if region is not None:
        settings.sliders['FOV Size'] = float(region)


def base_region_size(settings: 'AiSettings', config: dict[str, Any]) -> float:
    """Base FOV (profile or Setup override)."""
    if config.get('ai_region_size') is not None:
        return float(config.get('ai_region_size'))
    return float(settings.sliders.get('FOV Size', 200))


def effective_region_size(settings: 'AiSettings', config: dict[str, Any], *, use_dynamic: bool = False) -> float:
    """FOV used for target filter / debug overlay."""
    base = base_region_size(settings, config)
    if not use_dynamic or not settings.toggles.get('Dynamic FOV', False):
        return base
    dynamic = float(settings.sliders.get('Dynamic FOV Size', base))
    return min(base, dynamic) if dynamic > 0 else base


# Backward-compatible alias for callers that only need the base size.
def effective_fov_size(
    settings: 'AiSettings',
    config: dict[str, Any],
    *,
    use_dynamic: bool = False,
) -> float:
    return effective_region_size(settings, config, use_dynamic=use_dynamic)


def import_profile_dict(data: dict[str, Any], settings: 'AiSettings') -> None:
    """Load profile dict using short alias keys or legacy internal keys."""
    for alias_key, legacy_key in PROFILE_ALIAS_MAP.items():
        if alias_key in data:
            _apply_value(settings, legacy_key, data[alias_key])
    for key, value in data.items():
        if key in settings.toggles or key in settings.sliders or key in settings.dropdowns:
            _apply_value(settings, key, value)


def export_profile_dict(settings: 'AiSettings') -> dict[str, Any]:
    """Export profile using short alias keys for portable .cfg files."""
    out: dict[str, Any] = {}
    for alias_key, legacy_key in PROFILE_ALIAS_MAP.items():
        if legacy_key in settings.toggles:
            out[alias_key] = settings.toggles[legacy_key]
        elif legacy_key in settings.sliders:
            out[alias_key] = settings.sliders[legacy_key]
        elif legacy_key in settings.dropdowns:
            out[alias_key] = settings.dropdowns[legacy_key]
    return out


def _apply_value(settings: 'AiSettings', key: str, value: Any) -> None:
    if key in settings.toggles:
        settings.toggles[key] = bool(value)
    elif key in settings.sliders:
        settings.sliders[key] = float(value)
    elif key in settings.dropdowns:
        settings.dropdowns[key] = str(value)
