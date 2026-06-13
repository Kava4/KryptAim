"""AI engine API for rebuild web UI."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from app.ai.community_models import community_models_status, download_community_model, models_dir
from app.ai.lifecycle import invalidate_config_cache
from app.ai.model_classes import apply_team_to_player_class, class_info_for_path
from app.core.licensing import ai_access_status
from app.ai.ndi_control import get_ndi_sources, request_ndi_refresh
from app.ai.presets import apply_quickstart
from app.ai.status import get_ai_runtime_status
from app.bootstrap.runtime import bootstrap_status
from app.core.config import load_config, save_config
from app.makcu.manager import makcu_manager
from web.input_status import get_input_status

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

_MODEL_EXTS = {'.pt', '.onnx', '.engine'}


def _ai_gate():
    status = ai_access_status()
    if status.get('allowed'):
        return None
    return (
        jsonify(
            {
                'success': False,
                'message': status.get('message') or 'AI requires a supporter license',
                'ai_access': status,
                'locked': True,
            },
        ),
        403,
    )


def _list_models() -> list[str]:
    names: list[str] = []
    for path in sorted(models_dir().iterdir()):
        if path.is_file() and path.suffix.lower() in _MODEL_EXTS:
            names.append(path.name)
    return names


def _resolve_model_path(name: str) -> str:
    raw = (name or '').strip()
    if not raw:
        return ''
    path = Path(raw)
    if path.is_file():
        return str(path)
    candidate = models_dir() / raw
    if candidate.is_file():
        return str(candidate)
    return raw


def _parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {'1', 'true', 'on', 'yes'}


def _merge_config(updates: dict) -> dict:
    config = load_config()
    config.update(updates)
    save_config(config)
    invalidate_config_cache()
    return config


def _model_class_payload(config: dict) -> dict:
    path = str(config.get('ai_model_path', '') or '').strip()
    info = class_info_for_path(path)
    return {
        **info,
        'ai_player_class': str(config.get('ai_player_class', '') or ''),
        'ai_head_class': str(config.get('ai_head_class', '') or ''),
        'ai_my_team': str(config.get('ai_my_team', '') or '').lower(),
    }


def _merge_with_team(updates: dict) -> dict:
    config = load_config()
    config.update(updates)
    team_updates = apply_team_to_player_class(config)
    if team_updates:
        updates = {**updates, **team_updates}
    return updates


def _cuda_info() -> tuple[bool, str]:
    try:
        import torch

        if torch.cuda.is_available():
            return True, torch.cuda.get_device_name(0)
    except Exception:
        pass
    return False, ''


def _status_payload() -> dict:
    config = load_config()
    runtime = get_ai_runtime_status()
    cuda_ok, cuda_name = _cuda_info()
    input_status = get_input_status()
    makcu_ok = bool(input_status['makcu_hardware'])
    makcu_dev = bool(input_status['makcu_dev_fallback'])
    model_path = str(config.get('ai_model_path', '') or '').strip()
    model_name = Path(model_path).name if model_path else ''
    aim_key = (config.get('ai_aim_keybind') or 'M4').strip()
    aim_active = makcu_ok and makcu_manager.get_button_state(aim_key)
    pressed = [k for k in ('LMB', 'RMB', 'MMB', 'M4', 'M5') if makcu_manager.get_button_state(k)]

    readiness = []
    if not makcu_ok:
        label = 'Makcu connected (dev fallback)' if makcu_dev else 'Makcu connected'
        readiness.append({'ok': False, 'label': label})
    else:
        readiness.append({'ok': True, 'label': 'Makcu connected'})
    if runtime.ndi_connected and runtime.ndi_has_video:
        readiness.append({'ok': True, 'label': 'NDI video'})
    elif config.get('ai_capture_mode', 'ndi') == 'ndi':
        readiness.append({'ok': False, 'label': 'NDI video'})
    if runtime.model_loaded:
        readiness.append({'ok': True, 'label': 'Model loaded'})
    else:
        readiness.append({'ok': False, 'label': 'Model loaded'})
    if config.get('ai_enabled'):
        readiness.append({'ok': True, 'label': 'Engine running'})
    else:
        readiness.append({'ok': False, 'label': 'Engine running'})

    bs = bootstrap_status()
    access = ai_access_status()
    return {
        'ai_access': access,
        'enabled': bool(config.get('ai_enabled')),
        'bootstrap': bs,
        'ai_engine_enabled': bool(config.get('ai_enabled')),
        'running': bool(config.get('ai_enabled')),
        'state': runtime.state,
        'detail': runtime.detail,
        'fps': round(runtime.capture_fps, 1),
        'last_confidence': runtime.detection_count,
        'latency_inference_ms': round(runtime.inference_ms, 1),
        'latency_grab_ms': 0,
        'latency_trigger_ms': 0,
        'model_loaded': runtime.model_loaded,
        'configured_model': model_name or 'None',
        'active_model': model_name or 'None',
        'models': _list_models(),
        'active_config': 'config.json',
        'configs': ['config.json'],
        'ndi_sources': get_ndi_sources(),
        'capture_mode': config.get('ai_capture_mode', 'ndi'),
        'ndi_connected': runtime.ndi_connected,
        'ndi_has_video': runtime.ndi_has_video,
        'ndi_source': runtime.ndi_source or config.get('ai_ndi_source', ''),
        'makcu_connected': makcu_ok,
        'makcu_dev_fallback': makcu_dev,
        'makcu_buttons_live': makcu_ok,
        'makcu_buttons_pressed': pressed,
        'aim_key_active': aim_active,
        'aim_assist_on': bool(config.get('ai_aim_enabled')),
        'auto_trigger_on': bool(config.get('ai_trigger_enabled')),
        'trigger_always_on': bool(config.get('ai_trigger_always_on')),
        'trigger_key_active': aim_active,
        'trigger_block_reason': runtime.last_block_reason,
        'trigger_armed': runtime.trigger_armed,
        'inference_backend': 'cuda_ultralytics',
        'active_provider': 'CUDA' if cuda_ok else 'CPU',
        'cuda_available': cuda_ok,
        'cuda_device_name': cuda_name,
        'onnx_ready': True,
        'portable_build': False,
        'movement_mode': config.get('ai_assist_mode', 'trigger'),
        'movement_path': '',
        'last_error': runtime.detail if runtime.state == 'error' else '',
        'readiness': readiness,
        'profiles': [],
        'assist_mode': config.get('ai_assist_mode', 'trigger'),
        'aim_point': config.get('ai_aim_point', 'head'),
        'detection_conf': config.get('ai_detection_conf', 0.25),
        **_model_class_payload(config),
    }


@ai_bp.route('/status', methods=['GET'])
def ai_status():
    try:
        return jsonify({'success': True, **_status_payload()})
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500


@ai_bp.route('/enable', methods=['POST'])
def ai_enable():
    denied = _ai_gate()
    if denied:
        return denied
    enabled = _parse_bool(request.form.get('enabled', request.form.get('ai_engine_enabled', False)))
    _merge_config({'ai_enabled': enabled})
    return jsonify({'success': True, 'enabled': enabled})


@ai_bp.route('/quickstart', methods=['POST'])
def ai_quickstart():
    denied = _ai_gate()
    if denied:
        return denied
    preset = (request.form.get('preset') or '').strip().lower()
    trigger_only = preset == 'trigger' or _parse_bool(request.form.get('trigger_only', False))
    aim_only = preset == 'aim' or _parse_bool(request.form.get('aim_only', False))
    updates = apply_quickstart(trigger_only=trigger_only, aim_only=aim_only)
    config = _merge_config(updates)
    return jsonify({'success': True, 'config': config, 'preset': preset or 'both'})


@ai_bp.route('/ndi/refresh', methods=['GET', 'POST'])
def ai_ndi_refresh():
    denied = _ai_gate()
    if denied:
        return denied
    request_ndi_refresh()
    return jsonify({'success': True, 'sources': get_ndi_sources()})


@ai_bp.route('/capture', methods=['POST'])
def ai_capture():
    denied = _ai_gate()
    if denied:
        return denied
    updates = {
        'ai_capture_mode': (request.form.get('capture_mode') or 'ndi').strip(),
        'ai_ndi_source': (request.form.get('ndi_source') or '').strip(),
    }
    for key, field in (
        ('ai_main_pc_width', 'main_pc_width'),
        ('ai_main_pc_height', 'main_pc_height'),
        ('ai_region_size', 'region_size'),
    ):
        raw = request.form.get(field)
        if raw is not None and str(raw).strip():
            try:
                updates[key] = int(raw)
            except ValueError:
                pass
    _merge_config(updates)
    request_ndi_refresh()
    return jsonify({'success': True})


@ai_bp.route('/detection', methods=['POST'])
def ai_detection():
    denied = _ai_gate()
    if denied:
        return denied
    updates: dict = {}
    conf = request.form.get('conf')
    if conf is not None and str(conf).strip():
        try:
            updates['ai_detection_conf'] = float(conf)
        except ValueError:
            pass
    model = request.form.get('model_path') or request.form.get('model')
    if model is not None:
        updates['ai_model_path'] = _resolve_model_path(model)
    aim_point = request.form.get('aim_point')
    if aim_point:
        updates['ai_aim_point'] = aim_point.strip().lower()
    mode = request.form.get('assist_mode')
    if mode:
        updates['ai_assist_mode'] = mode.strip().lower()
    for key in ('ai_player_class', 'ai_head_class'):
        if request.form.get(key) is not None:
            updates[key] = str(request.form.get(key, '') or '').strip()
    if request.form.get('ai_my_team') is not None:
        updates['ai_my_team'] = str(request.form.get('ai_my_team', '') or '').strip().lower()
    if updates:
        updates = _merge_with_team(updates)
        _merge_config(updates)
    return jsonify({'success': True, **_model_class_payload(load_config())})


@ai_bp.route('/model/select', methods=['POST'])
def ai_model_select():
    denied = _ai_gate()
    if denied:
        return denied
    name = (request.form.get('model') or request.form.get('filename') or '').strip()
    path = _resolve_model_path(name)
    updates = _merge_with_team({'ai_model_path': path})
    _merge_config(updates)
    return jsonify({'success': True, 'model': name, **_model_class_payload(load_config())})


@ai_bp.route('/community/models', methods=['GET'])
def ai_community_models():
    denied = _ai_gate()
    if denied:
        return denied
    try:
        payload = community_models_status()
        return jsonify({'success': True, **payload})
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500


@ai_bp.route('/community/download', methods=['POST'])
def ai_community_download():
    denied = _ai_gate()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    name = (request.form.get('filename') or request.form.get('model') or data.get('filename') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Missing filename'}), 400
    path, message = download_community_model(name)
    if path is None:
        return jsonify({'success': False, 'message': message}), 502
    updates = _merge_with_team({'ai_model_path': str(path)})
    _merge_config(updates)
    return jsonify(
        {
            'success': True,
            'message': message,
            'model': path.name,
            'models': _list_models(),
            **_model_class_payload(load_config()),
        },
    )


@ai_bp.route('/models/upload', methods=['POST'])
def ai_model_upload():
    denied = _ai_gate()
    if denied:
        return denied
    uploaded = request.files.get('model_file') or request.files.get('file')
    if not uploaded or not uploaded.filename:
        return jsonify({'success': False, 'message': 'No file uploaded.'}), 400
    name = secure_filename(uploaded.filename)
    if Path(name).suffix.lower() not in _MODEL_EXTS:
        return jsonify({'success': False, 'message': 'Use .pt, .onnx, or .engine'}), 400
    dest = models_dir() / name
    uploaded.save(dest)
    updates = _merge_with_team({'ai_model_path': str(dest)})
    _merge_config(updates)
    return jsonify(
        {
            'success': True,
            'models': _list_models(),
            'model': name,
            **_model_class_payload(load_config()),
        },
    )


@ai_bp.route('/toggle', methods=['POST'])
def ai_toggle():
    """Map legacy toggle names to flat config keys."""
    denied = _ai_gate()
    if denied:
        return denied
    name = (request.form.get('toggle') or request.form.get('name') or '').strip()
    value = _parse_bool(request.form.get('value', request.form.get('enabled', False)))
    mapping = {
        'Aim Assist': 'ai_aim_enabled',
        'Auto Trigger': 'ai_trigger_enabled',
        'Always-on aim': 'ai_aim_always_on',
        'Trigger always on': 'ai_trigger_always_on',
        'Spray block': 'ai_trigger_spray_block',
    }
    key = mapping.get(name)
    if not key:
        return jsonify({'success': False, 'message': f'Unknown toggle: {name}'}), 400
    _merge_config({key: value})
    return jsonify({'success': True})


@ai_bp.route('/slider', methods=['POST'])
def ai_slider():
    denied = _ai_gate()
    if denied:
        return denied
    name = (request.form.get('slider') or request.form.get('name') or '').strip()
    try:
        value = float(request.form.get('value', 0))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid value'}), 400
    mapping = {
        'Trigger radius': 'ai_trigger_radius_px',
        'Trigger delay': 'ai_trigger_delay_ms',
        'Trigger cooldown': 'ai_trigger_cooldown_ms',
        'Trigger min conf': 'ai_trigger_min_conf',
        'Click hold': 'ai_trigger_click_hold_ms',
        'Prediction': 'ai_trigger_prediction_ms',
        'Aim speed': 'ai_aim_speed',
        'Aim max px': 'ai_aim_max_px',
        'Detection conf': 'ai_detection_conf',
    }
    key = mapping.get(name)
    if not key:
        return jsonify({'success': False, 'message': f'Unknown slider: {name}'}), 400
    if key.endswith('_px') or key.endswith('_ms'):
        value = int(value)
    _merge_config({key: value})
    return jsonify({'success': True})


@ai_bp.route('/dropdown', methods=['POST'])
def ai_dropdown():
    denied = _ai_gate()
    if denied:
        return denied
    name = (request.form.get('dropdown') or request.form.get('name') or '').strip()
    value = (request.form.get('value') or '').strip()
    if name in {'Assist mode', 'assist_mode'}:
        _merge_config({'ai_assist_mode': value.lower()})
    elif name in {'Aim point', 'aim_point'}:
        _merge_config({'ai_aim_point': value.lower()})
    elif name in {'Aim key', 'Trigger key'}:
        key = 'ai_aim_keybind' if 'Aim' in name else 'ai_trigger_keybind'
        _merge_config({key: value.upper()})
    return jsonify({'success': True})


@ai_bp.route('/settings', methods=['GET'])
def ai_settings():
    config = load_config()
    return jsonify({
        'success': True,
        'active_config': 'config.json',
        'toggles': {
            'Aim Assist': bool(config.get('ai_aim_enabled')),
            'Auto Trigger': bool(config.get('ai_trigger_enabled')),
            'Always-on aim': bool(config.get('ai_aim_always_on')),
            'Trigger always on': bool(config.get('ai_trigger_always_on')),
        },
        'sliders': {
            'Trigger radius': config.get('ai_trigger_radius_px', 8),
            'Trigger delay': config.get('ai_trigger_delay_ms', 30),
            'Trigger cooldown': config.get('ai_trigger_cooldown_ms', 120),
            'Prediction': config.get('ai_trigger_prediction_ms', 35),
            'Aim speed': config.get('ai_aim_speed', 1.0),
            'Aim max px': config.get('ai_aim_max_px', 280),
            'Detection conf': config.get('ai_detection_conf', 0.25),
        },
        'dropdowns': {
            'Assist mode': config.get('ai_assist_mode', 'trigger'),
            'Aim point': config.get('ai_aim_point', 'head'),
            'Aim key': config.get('ai_aim_keybind', 'M4'),
            'Trigger key': config.get('ai_trigger_keybind', 'M4'),
        },
    })
