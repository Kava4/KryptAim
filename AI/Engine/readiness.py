"""AimSync AI readiness checklist for UI and quick-start."""

from __future__ import annotations

from typing import Any

from AI.Engine.models import list_local_models, resolve_model_path
from AI.Engine.settings import AiSettings
from Config.config_manager import get_ai_configs_dir, load_config


def build_readiness(
    *,
    status: dict[str, Any],
    settings: AiSettings | None = None,
) -> dict[str, Any]:
    config = load_config()
    cfg_name = config.get('ai_active_config', 'Default.cfg') or 'Default.cfg'
    cfg_path = get_ai_configs_dir() / cfg_name
    models = list_local_models()
    configured_model = (config.get('ai_active_model') or '').strip()
    capture_mode = (config.get('ai_capture_mode') or 'ndi').strip().lower()
    ndi_source = (config.get('ai_ndi_source') or '').strip()
    aim_assist = bool((settings or AiSettings()).toggles.get('Aim Assist'))
    auto_trigger = bool((settings or AiSettings()).toggles.get('Auto Trigger'))
    constant_track = bool((settings or AiSettings()).toggles.get('Constant AI Tracking'))
    always_on_aim = bool(config.get('ai_always_on_aim'))
    trigger_always_on = bool(config.get('ai_trigger_always_on'))
    aim_key = (config.get('ai_aim_keybind') or 'None').strip()
    has_aim_hold = (
        constant_track
        or always_on_aim
        or trigger_always_on
        or (aim_key and aim_key.lower() != 'none')
    )
    num_classes = 1
    if status.get('model_loaded') and status.get('model_classes'):
        num_classes = max(len(status['model_classes']), 1)
    player_class = (config.get('ai_player_class') or '').strip()

    items: list[dict[str, Any]] = [
        {
            'id': 'makcu',
            'ok': bool(status.get('makcu_connected')),
            'label': 'Makcu connected (moves gaming mouse)',
            'required': True,
        },
        {
            'id': 'engine',
            'ok': bool(config.get('ai_engine_enabled')),
            'label': 'AI engine running',
            'required': True,
        },
        {
            'id': 'model',
            'ok': bool(configured_model and status.get('model_loaded')),
            'label': 'Model selected and loaded',
            'required': True,
        },
        {
            'id': 'model_file',
            'ok': bool(configured_model and resolve_model_path(configured_model)),
            'label': 'Model file exists in bin/models',
            'required': True,
        },
        {
            'id': 'cfg',
            'ok': cfg_path.is_file(),
            'label': f'Aim profile {cfg_name}',
            'required': True,
        },
        {
            'id': 'feature',
            'ok': aim_assist or auto_trigger,
            'label': 'Aim Assist or Auto Trigger on (in .cfg)',
            'required': True,
        },
        {
            'id': 'aim_hold',
            'ok': has_aim_hold,
            'label': 'Aim/trigger key, Always-on aim, or Trigger always on',
            'required': True,
        },
        {
            'id': 'capture_ndi',
            'ok': capture_mode != 'ndi' or bool(ndi_source),
            'label': 'NDI source selected (dual-PC)',
            'required': capture_mode == 'ndi',
        },
        {
            'id': 'onnx',
            'ok': bool(status.get('onnx_ready')) or status.get('inference_backend') == 'cuda_ultralytics',
            'label': 'AI dependencies installed',
            'required': True,
        },
        {
            'id': 'player_class',
            'ok': num_classes <= 1 or bool(player_class),
            'label': 'Player class set (e.g. 0) for multi-class models',
            'required': num_classes > 1,
        },
    ]

    if not models:
        items.append({
            'id': 'models_dir',
            'ok': False,
            'label': 'At least one model in bin/models (upload local .onnx)',
            'required': True,
        })

    required = [i for i in items if i.get('required')]
    ready = all(i['ok'] for i in required)
    return {
        'ready': ready,
        'items': items,
        'hint': _hint(ready, items, capture_mode, models),
    }


def _hint(ready: bool, items: list[dict], capture_mode: str, models: list[str]) -> str:
    if ready:
        return 'Ready: hold RMB on gaming mouse (Makcu) or enable Always-on aim / Trigger always on.'
    failed = [i['label'] for i in items if i.get('required') and not i['ok']]
    if not models:
        return 'Upload a .onnx model to bin/models or use the AI panel upload.'
    if capture_mode == 'ndi' and any('NDI' in f for f in failed):
        return 'Install NDI on gaming PC, start OBS/virtual cam NDI output, refresh NDI source here.'
    if any('Makcu' in f for f in failed):
        return 'Connect Makcu on this PC (AimSync PC) — required for dual-PC mouse control.'
    if any('Aim Assist' in f for f in failed):
        return 'Turn on Aim Assist in Profile settings or click Quick setup.'
    if any('Aim/trigger' in f for f in failed):
        return 'Dual-PC: connect Makcu and hold RMB on gaming mouse, or enable Always-on aim / Trigger always on.'
    return 'Complete the checklist below, then Quick setup if needed.'
