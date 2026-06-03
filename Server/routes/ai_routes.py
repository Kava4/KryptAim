"""Beta-only API routes for the AI / trigger engine."""

from __future__ import annotations

import json

from flask import Blueprint, jsonify, request

from Config.app_identity import is_beta_channel
from Config.config_manager import get_ai_configs_dir, load_config, save_config
from AI.Engine.engine import get_ai_engine
from AI.Engine.models import (
    GITHUB_CONFIGS_API,
    GITHUB_MODELS_API,
    delete_model,
    download_store_file,
    fetch_store_listing,
    list_local_configs,
    list_local_models,
    save_uploaded_model,
)
from AI.Engine.settings import (
    DEFAULT_DROPDOWNS,
    DEFAULT_SLIDERS,
    DEFAULT_TOGGLES,
    DROPDOWN_OPTIONS,
    SLIDER_SPECS,
    TOGGLE_GROUPS,
)
from Recoil.hotkeys import HotkeyValidationError, normalize_hotkey_string, validate_hotkey_bindings

ai_bp = Blueprint('ai_bp', __name__, url_prefix='/api/ai')


def _beta_guard():
    if not is_beta_channel():
        return jsonify({'success': False, 'message': 'AI engine is available only in beta.'}), 404
    return None


def _parse_bool(value) -> bool:
    return str(value).lower() in {'1', 'true', 'on', 'yes'}


@ai_bp.before_request
def _require_beta():
    response = _beta_guard()
    if response is not None:
        return response


@ai_bp.route('/status', methods=['GET'])
def ai_status():
    engine = get_ai_engine()
    payload = engine.get_status_dict()
    config = load_config()
    payload['configs'] = list_local_configs()
    payload['ai_engine_enabled'] = bool(config.get('ai_engine_enabled'))
    try:
        import onnxruntime  # noqa: F401

        payload['onnx_ready'] = True
    except ImportError:
        payload['onnx_ready'] = False
    return jsonify({'success': True, **payload})


@ai_bp.route('/settings', methods=['GET'])
def ai_settings():
    engine = get_ai_engine()
    config = load_config()
    filename = config.get('ai_active_config', 'Default.cfg')
    engine.settings.load_cfg(filename)
    return jsonify({
        'success': True,
        'toggles': engine.settings.toggles,
        'sliders': engine.settings.sliders,
        'dropdowns': engine.settings.dropdowns,
        'active_config': filename,
    })


@ai_bp.route('/config/content', methods=['GET'])
def ai_config_content():
    config = load_config()
    filename = request.args.get('filename') or config.get('ai_active_config', 'Default.cfg')
    engine = get_ai_engine()
    try:
        data = engine.settings.read_cfg_file(filename)
    except (OSError, json.JSONDecodeError) as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    return jsonify({
        'success': True,
        'filename': filename,
        'content': json.dumps(data, indent=2),
    })


@ai_bp.route('/config/editor/save', methods=['POST'])
def ai_config_editor_save():
    config = load_config()
    filename = (request.form.get('filename') or config.get('ai_active_config', 'Default.cfg')).strip()
    raw = request.form.get('content', '')
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError('Config must be a JSON object.')
    except (json.JSONDecodeError, ValueError) as exc:
        return jsonify({'success': False, 'message': f'Invalid JSON: {exc}'}), 400

    engine = get_ai_engine()
    engine.settings.write_cfg_file(filename, data)
    if config.get('ai_active_config') == filename:
        engine.invalidate_load_cache()
        engine.reload_from_config()
    return jsonify({'success': True, 'filename': filename})


@ai_bp.route('/config/upload', methods=['POST'])
def ai_config_upload():
    uploaded = request.files.get('config_file')
    if not uploaded or not uploaded.filename:
        return jsonify({'success': False, 'message': 'No file uploaded.'}), 400
    name = uploaded.filename
    if not name.lower().endswith('.cfg'):
        return jsonify({'success': False, 'message': 'Only .cfg files are supported.'}), 400
    try:
        data = json.loads(uploaded.read().decode('utf-8'))
        if not isinstance(data, dict):
            raise ValueError('Config must be a JSON object.')
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return jsonify({'success': False, 'message': f'Invalid config file: {exc}'}), 400

    engine = get_ai_engine()
    engine.settings.write_cfg_file(name, data)
    return jsonify({'success': True, 'filename': name, 'configs': list_local_configs()})


@ai_bp.route('/config/select', methods=['POST'])
def ai_select_config():
    config = load_config()
    cfg = (request.form.get('ai_active_config') or 'Default.cfg').strip()
    config['ai_active_config'] = cfg
    save_config(config)
    engine = get_ai_engine()
    engine.invalidate_load_cache()
    engine.reload_from_config()
    return jsonify({
        'success': True,
        'config': cfg,
        'toggles': engine.settings.toggles,
        'sliders': engine.settings.sliders,
        'dropdowns': engine.settings.dropdowns,
    })


@ai_bp.route('/enable', methods=['POST'])
def ai_enable():
    config = load_config()
    config['ai_engine_enabled'] = _parse_bool(request.form.get('ai_engine_enabled', 'off'))
    save_config(config)
    get_ai_engine().reload_from_config()
    return jsonify({'success': True, 'enabled': config['ai_engine_enabled']})


@ai_bp.route('/model/select', methods=['POST'])
def ai_select_model():
    config = load_config()
    model = (request.form.get('ai_active_model') or '').strip()
    config['ai_active_model'] = model
    save_config(config)
    engine = get_ai_engine()
    engine.invalidate_load_cache()
    engine.reload_from_config()
    status = engine.get_status_dict()
    return jsonify({
        'success': True,
        'model': model,
        'model_loaded': status.get('model_loaded'),
        'last_error': status.get('last_error', ''),
    })


@ai_bp.route('/config/save', methods=['POST'])
def ai_save_config():
    engine = get_ai_engine()
    config = load_config()
    filename = config.get('ai_active_config', 'Default.cfg')
    for key, value in request.form.items():
        if key in engine.settings.toggles:
            engine.settings.toggles[key] = _parse_bool(value)
        elif key in engine.settings.sliders:
            try:
                engine.settings.sliders[key] = float(value)
            except ValueError:
                pass
    engine.settings.save_cfg(filename)
    save_config(config)
    return jsonify({'success': True})


@ai_bp.route('/toggle', methods=['POST'])
def ai_toggle():
    engine = get_ai_engine()
    name = request.form.get('toggle_name', '')
    if name not in engine.settings.toggles:
        return jsonify({'success': False, 'message': 'Unknown toggle.'}), 400
    engine.settings.toggles[name] = _parse_bool(request.form.get('enabled', 'off'))
    config = load_config()
    engine.settings.save_cfg(config.get('ai_active_config', 'Default.cfg'))
    return jsonify({'success': True, 'toggle': name, 'enabled': engine.settings.toggles[name]})


@ai_bp.route('/dropdown', methods=['POST'])
def ai_dropdown():
    engine = get_ai_engine()
    name = request.form.get('dropdown_name', '')
    if name not in engine.settings.dropdowns:
        return jsonify({'success': False, 'message': 'Unknown dropdown.'}), 400
    value = (request.form.get('value') or '').strip()
    engine.settings.dropdowns[name] = value
    config = load_config()
    engine.settings.save_cfg(config.get('ai_active_config', 'Default.cfg'))
    if name == 'Image Size':
        engine.invalidate_load_cache()
        engine.reload_from_config()
    return jsonify({'success': True, 'dropdown': name, 'value': value})


@ai_bp.route('/slider', methods=['POST'])
def ai_slider():
    engine = get_ai_engine()
    name = request.form.get('slider_name', '')
    if name not in engine.settings.sliders:
        return jsonify({'success': False, 'message': 'Unknown slider.'}), 400
    try:
        engine.settings.sliders[name] = float(request.form.get('value', engine.settings.sliders[name]))
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid value.'}), 400
    config = load_config()
    engine.settings.save_cfg(config.get('ai_active_config', 'Default.cfg'))
    return jsonify({'success': True})


@ai_bp.route('/keybind', methods=['POST'])
def ai_keybind():
    """Legacy endpoint — prefer Global Settings → Custom Hotkeys (/api/recoil/hotkeys)."""
    config = load_config()
    field = request.form.get('field', '')
    value = normalize_hotkey_string((request.form.get('value') or '').strip())
    if field == 'ai_aim_keybind':
        config['ai_aim_keybind'] = value
    elif field == 'ai_second_aim_keybind':
        config['ai_second_aim_keybind'] = value
    elif field == 'ai_engine_toggle_hotkey':
        config['ai_engine_toggle_hotkey'] = value
    else:
        return jsonify({'success': False, 'message': 'Unknown keybind field.'}), 400
    try:
        validate_hotkey_bindings(
            config.get('global_toggle_hotkey'),
            config.get('weapon_cycle_hotkey'),
            config.get('weapon_direct_binds'),
            ai_aim_keybind=config.get('ai_aim_keybind'),
            ai_second_aim_keybind=config.get('ai_second_aim_keybind'),
            ai_engine_toggle_hotkey=config.get('ai_engine_toggle_hotkey'),
        )
    except HotkeyValidationError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    save_config(config)
    return jsonify({'success': True})


@ai_bp.route('/models/upload', methods=['POST'])
def ai_upload_model():
    uploaded = request.files.get('model_file')
    if not uploaded or not uploaded.filename:
        return jsonify({'success': False, 'message': 'No file uploaded.'}), 400
    try:
        path = save_uploaded_model(uploaded.filename, uploaded.read())
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    return jsonify({'success': True, 'filename': path.name, 'models': list_local_models()})


@ai_bp.route('/models/delete', methods=['POST'])
def ai_delete_model():
    name = (request.form.get('filename') or '').strip()
    if delete_model(name):
        return jsonify({'success': True, 'models': list_local_models()})
    return jsonify({'success': False, 'message': 'Model not found.'}), 404


@ai_bp.route('/store/list', methods=['GET'])
def ai_store_list():
    folder = request.args.get('folder', 'models')
    api = GITHUB_MODELS_API if folder == 'models' else GITHUB_CONFIGS_API
    try:
        names = fetch_store_listing(api)
        local = list_local_models() if folder == 'models' else list_local_configs()
        available = [n for n in names if n not in local]
        return jsonify({'success': True, 'folder': folder, 'available': available})
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 502


@ai_bp.route('/store/download', methods=['POST'])
def ai_store_download():
    folder = request.form.get('folder', 'models')
    filename = (request.form.get('filename') or '').strip()
    if not filename:
        return jsonify({'success': False, 'message': 'Missing filename.'}), 400
    try:
        download_store_file(folder, filename)
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 502
    return jsonify({
        'success': True,
        'models': list_local_models(),
        'configs': list_local_configs(),
    })


@ai_bp.route('/defaults', methods=['GET'])
def ai_defaults():
    return jsonify({
        'success': True,
        'toggles': DEFAULT_TOGGLES,
        'sliders': DEFAULT_SLIDERS,
        'dropdowns': DEFAULT_DROPDOWNS,
        'slider_specs': SLIDER_SPECS,
        'dropdown_options': DROPDOWN_OPTIONS,
        'toggle_groups': TOGGLE_GROUPS,
    })


@ai_bp.route('/config/create-default', methods=['POST'])
def ai_create_default_config():
    path = get_ai_configs_dir() / 'Default.cfg'
    if not path.is_file():
        from AI.Engine.settings import AiSettings

        settings = AiSettings()
        settings.save_cfg('Default.cfg')
    return jsonify({'success': True, 'configs': list_local_configs()})
