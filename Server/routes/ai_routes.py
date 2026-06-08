"""API routes for the AI / trigger engine."""

from __future__ import annotations

import json

from flask import Blueprint, Response, jsonify, request

from Config.config_manager import get_ai_configs_dir, load_config, save_config
from AI.Engine.engine import get_ai_engine
from AI.Engine.inference_backend import default_inference_backend, probe_gpu_status
from AI.Engine.models import (
    COMMUNITY_STORE_MESSAGE,
    delete_model,
    download_store_file,
    list_local_configs,
    list_local_models,
    save_uploaded_model,
)
from AI.Engine.profiles import apply_profile, list_profiles, save_profile
from AI.Engine.settings import (
    DEFAULT_DROPDOWNS,
    DEFAULT_SLIDERS,
    DEFAULT_TOGGLES,
    DROPDOWN_OPTIONS,
    BASELINE_DROPDOWNS,
    BASELINE_SLIDERS,
    BASELINE_TOGGLES,
    SLIDER_SPECS,
    TOGGLE_GROUPS,
    AiSettings,
    apply_default_ai_profile,
    apply_starter_profile,
    is_experimental_dropdown,
    is_experimental_slider,
    is_experimental_toggle,
)
from Recoil.hotkeys import HotkeyValidationError, normalize_hotkey_string, validate_hotkey_bindings

ai_bp = Blueprint('ai_bp', __name__, url_prefix='/api/ai')


def _parse_bool(value) -> bool:
    return str(value).lower() in {'1', 'true', 'on', 'yes'}


@ai_bp.route('/status', methods=['GET'])
def ai_status():
    try:
        engine = get_ai_engine()
        payload = engine.get_status_dict()
        config = load_config()
        payload['configs'] = list_local_configs()
        payload['profiles'] = list_profiles()
        payload['ai_engine_enabled'] = bool(config.get('ai_engine_enabled'))
        try:
            import onnxruntime  # noqa: F401

            payload['onnx_ready'] = True
        except ImportError:
            payload['onnx_ready'] = False
        return jsonify({'success': True, **payload})
    except Exception as exc:
        import logging

        logging.getLogger('AimSync.AI.Routes').exception('ai_status failed')
        return jsonify({'success': False, 'message': str(exc)}), 500


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
        engine.request_reload()
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
    engine.request_reload()
    return jsonify({
        'success': True,
        'config': cfg,
        'toggles': engine.settings.toggles,
        'sliders': engine.settings.sliders,
        'dropdowns': engine.settings.dropdowns,
    })


@ai_bp.route('/inference_backend', methods=['POST'])
def ai_inference_backend():
    config = load_config()
    backend = (request.form.get('ai_inference_backend') or 'directml').strip().lower()
    allowed = {'directml', 'cuda_onnx', 'cuda_ultralytics', 'cpu'}
    if backend not in allowed:
        return jsonify({'success': False, 'message': f'Unknown backend. Use one of: {", ".join(sorted(allowed))}'}), 400
    config['ai_inference_backend'] = backend
    save_config(config)
    engine = get_ai_engine()
    engine.invalidate_load_cache()
    if not engine.request_reload(wait_timeout=120.0):
        return jsonify({'success': False, 'message': 'Model reload timed out.'}), 504
    return jsonify({'success': True, 'backend': backend, **engine.get_status_dict()})


@ai_bp.route('/capture', methods=['POST'])
def ai_capture_settings():
    config = load_config()
    mode = (request.form.get('ai_capture_mode') or config.get('ai_capture_mode', 'ndi')).strip().lower()
    if mode not in {'ndi', 'mss'}:
        return jsonify({'success': False, 'message': 'Capture mode must be ndi or mss.'}), 400
    config['ai_capture_mode'] = mode
    if request.form.get('ai_ndi_source') is not None:
        config['ai_ndi_source'] = request.form.get('ai_ndi_source', '').strip()
    for key in ('ai_main_pc_width', 'ai_main_pc_height'):
        if request.form.get(key) is not None:
            try:
                config[key] = int(float(request.form.get(key)))
            except ValueError:
                return jsonify({'success': False, 'message': f'{key} must be numeric.'}), 400
    save_config(config)
    engine = get_ai_engine()
    engine.request_reload()
    return jsonify({
        'success': True,
        'capture_mode': mode,
        'ndi_sources': list(engine.capture._ndi_sources_cache),
        'ndi_connected': engine.capture._ndi.connected if mode == 'ndi' else False,
        'ndi_last_error': engine.capture._ndi.last_error if mode == 'ndi' else '',
    })


@ai_bp.route('/ndi/refresh', methods=['GET'])
def ai_ndi_refresh():
    engine = get_ai_engine()
    sources = engine.refresh_ndi_sources_sync(timeout=15.0)
    return jsonify({'success': True, 'ndi_sources': sources})


@ai_bp.route('/debug/frame', methods=['GET'])
def ai_debug_frame():
    engine = get_ai_engine()
    jpeg = engine.get_debug_jpeg()
    if not jpeg:
        return '', 204
    return Response(jpeg, mimetype='image/jpeg')


@ai_bp.route('/profiles/list', methods=['GET'])
def ai_profiles_list():
    return jsonify({'success': True, 'profiles': list_profiles()})


@ai_bp.route('/profiles/save', methods=['POST'])
def ai_profiles_save():
    name = (request.form.get('name') or 'Default').strip()
    try:
        path = save_profile(name)
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    return jsonify({'success': True, 'path': str(path), 'profiles': list_profiles()})


@ai_bp.route('/profiles/load', methods=['POST'])
def ai_profiles_load():
    name = (request.form.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Select a profile.'}), 400
    try:
        apply_profile(name)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    engine = get_ai_engine()
    engine.invalidate_load_cache()
    if not engine.request_reload(wait_timeout=120.0):
        return jsonify({'success': False, 'message': 'Profile applied but model reload timed out.'}), 504
    config = load_config()
    return jsonify({
        'success': True,
        'profiles': list_profiles(),
        **engine.get_status_dict(),
        'ai_player_class': config.get('ai_player_class', ''),
        'ai_head_class': config.get('ai_head_class', ''),
        'ai_detection_conf': config.get('ai_detection_conf', 0.25),
        'ai_imgsz': config.get('ai_imgsz', 640),
        'ai_max_detect': config.get('ai_max_detect', 50),
        'ai_ndi_source': config.get('ai_ndi_source', ''),
    })


@ai_bp.route('/detection', methods=['POST'])
def ai_detection_settings():
    config = load_config()
    for key in (
        'ai_player_class',
        'ai_head_class',
        'ai_aim_mode',
        'ai_aim_keybind',
    ):
        if request.form.get(key) is not None:
            val = request.form.get(key, '').strip()
            if key == 'ai_aim_keybind':
                val = val.lower()
            config[key] = val
    for key in ('ai_player_y_offset', 'ai_imgsz', 'ai_max_detect', 'ai_main_pc_width', 'ai_main_pc_height'):
        if request.form.get(key) is not None:
            try:
                config[key] = int(float(request.form.get(key, config.get(key, 0))))
            except ValueError:
                return jsonify({'success': False, 'message': f'{key} must be numeric.'}), 400
    if request.form.get('ai_detection_conf') is not None:
        try:
            config['ai_detection_conf'] = float(request.form.get('ai_detection_conf'))
        except ValueError:
            return jsonify({'success': False, 'message': 'ai_detection_conf must be a number.'}), 400
    if request.form.get('ai_in_game_sens') is not None:
        try:
            config['ai_in_game_sens'] = float(request.form.get('ai_in_game_sens'))
        except ValueError:
            return jsonify({'success': False, 'message': 'ai_in_game_sens must be a number.'}), 400
    float_keys = (
        'ai_trigger_min_conf',
        'ai_normal_x_speed',
        'ai_normal_y_speed',
        'ai_smooth_gravity',
        'ai_smooth_wind',
    )
    int_keys = (
        'ai_trigger_radius_px',
        'ai_trigger_delay_ms',
        'ai_trigger_cooldown_ms',
        'ai_trigger_linger_ms',
        'ai_bezier_segments',
        'ai_bezier_ctrl_x',
        'ai_bezier_ctrl_y',
        'ai_smooth_segments',
    )
    for key in float_keys:
        if request.form.get(key) is not None:
            try:
                config[key] = float(request.form.get(key))
            except ValueError:
                return jsonify({'success': False, 'message': f'{key} must be a number.'}), 400
    for key in int_keys:
        if request.form.get(key) is not None:
            try:
                config[key] = int(float(request.form.get(key)))
            except ValueError:
                return jsonify({'success': False, 'message': f'{key} must be numeric.'}), 400
    for key in ('ai_debug_preview', 'ai_debug_cv2_window', 'ai_always_on_aim', 'ai_trigger_always_on', 'ai_button_mask'):
        if request.form.get(key) is not None:
            config[key] = _parse_bool(request.form.get(key))
    for key in ('ai_mask_aim_button', 'ai_mask_trigger_button'):
        if request.form.get(key) is not None:
            config[key] = (request.form.get(key) or 'RMB').strip().upper()
    if request.form.get('ai_aim_humanization') is not None:
        try:
            config['ai_aim_humanization'] = max(0, min(20, int(float(request.form.get('ai_aim_humanization')))))
        except ValueError:
            return jsonify({'success': False, 'message': 'ai_aim_humanization must be 0–20.'}), 400
    for key in ('ai_normal_x_speed', 'ai_normal_y_speed'):
        if request.form.get(key) is not None:
            try:
                config[key] = float(request.form.get(key))
            except ValueError:
                return jsonify({'success': False, 'message': f'{key} must be numeric.'}), 400
    if request.form.get('ai_bezier_segments') is not None:
        try:
            config['ai_bezier_segments'] = int(float(request.form.get('ai_bezier_segments')))
        except ValueError:
            return jsonify({'success': False, 'message': 'ai_bezier_segments must be numeric.'}), 400
    if request.form.get('ai_region_size') is not None:
        try:
            config['ai_region_size'] = int(float(request.form.get('ai_region_size')))
        except ValueError:
            return jsonify({'success': False, 'message': 'ai_region_size must be numeric.'}), 400
    if request.form.get('ai_trigger_keybind') is not None:
        config['ai_trigger_keybind'] = request.form.get('ai_trigger_keybind', 'None').strip()
    save_config(config)
    engine = get_ai_engine()
    if config.get('ai_trigger_always_on'):
        engine.settings.toggles['Auto Trigger'] = True
        config['ai_trigger_enabled'] = True
        save_config(config)
    conf = float(config.get('ai_detection_conf', 0.25))
    if 'AI Minimum Confidence' in engine.settings.sliders:
        engine.settings.sliders['AI Minimum Confidence'] = round(conf * 100, 1)
    cfg_name = config.get('ai_active_config', 'Default.cfg')
    if cfg_name and engine.settings.sliders:
        engine.settings.save_cfg(cfg_name)
    engine.invalidate_load_cache()
    engine.request_reload()
    return jsonify({'success': True})


@ai_bp.route('/enable', methods=['POST'])
def ai_enable():
    config = load_config()
    config['ai_engine_enabled'] = _parse_bool(request.form.get('ai_engine_enabled', 'off'))
    save_config(config)
    engine = get_ai_engine()
    engine.request_reload()
    return jsonify({'success': True, 'enabled': config['ai_engine_enabled'], **engine.get_status_dict()})


@ai_bp.route('/quickstart', methods=['POST'])
def ai_quickstart():
    """One-click: enable engine, pick model/NDI, starter .cfg (non-blocking HTTP)."""
    try:
        config = load_config()
        engine = get_ai_engine()
        models = list_local_models()
        gpu = probe_gpu_status()
        if gpu.get('cuda_available'):
            config['ai_inference_backend'] = 'cuda_ultralytics'
        elif not (config.get('ai_inference_backend') or '').strip():
            config['ai_inference_backend'] = default_inference_backend()

        pt_models = [m for m in models if m.lower().endswith(('.pt', '.engine'))]
        onnx_models = [m for m in models if m.lower().endswith('.onnx')]
        pick = pt_models or onnx_models or models
        if pick and not (config.get('ai_active_model') or '').strip():
            config['ai_active_model'] = pick[0]

        sources = engine.capture.list_ndi_sources(force_refresh=True)
        if sources:
            config['ai_capture_mode'] = 'ndi'
            if not (config.get('ai_ndi_source') or '').strip():
                config['ai_ndi_source'] = sources[0]
        else:
            config['ai_capture_mode'] = 'mss'

        config['ai_detection_conf'] = float(config.get('ai_detection_conf', 0.25) or 0.25)
        config['ai_imgsz'] = int(config.get('ai_imgsz', 640) or 640)
        config['ai_engine_enabled'] = True
        if (config.get('ai_aim_keybind') or 'None').strip().lower() == 'none':
            config['ai_aim_keybind'] = 'rmb'

        cfg_name = config.get('ai_active_config', 'Default.cfg') or 'Default.cfg'
        cfg_path = get_ai_configs_dir() / cfg_name
        if not cfg_path.is_file():
            starter = AiSettings()
            apply_default_ai_profile(starter)
            starter.save_cfg(cfg_name)
        else:
            engine.settings.load_cfg(cfg_name)
            apply_default_ai_profile(engine.settings)
            engine.settings.save_cfg(cfg_name)

        config['ai_class_filter_mode'] = 'target_label'
        config['ai_aim_mode'] = 'normal'
        config['ai_aim_humanization'] = 0

        save_config(config)
        engine.invalidate_load_cache()

        return jsonify({
            'success': True,
            'message': (
                'Quick setup saved. Model loads in the background (watch status above). '
                'Dual-PC: hold RMB on the gaming PC.'
            ),
            'ai_player_class': config.get('ai_player_class', ''),
            'ai_detection_conf': config.get('ai_detection_conf'),
            'capture_mode': config.get('ai_capture_mode'),
            'ndi_sources': sources,
            'ai_active_model': config.get('ai_active_model', ''),
            'enabled': True,
        })
    except Exception as exc:
        return jsonify({'success': False, 'message': f'Quick setup failed: {exc}'}), 500


@ai_bp.route('/model/select', methods=['POST'])
def ai_select_model():
    config = load_config()
    model = (request.form.get('ai_active_model') or '').strip()
    config['ai_active_model'] = model
    save_config(config)
    engine = get_ai_engine()
    if _parse_bool(request.form.get('force_reload', 'off')):
        engine._loaded_model = ''
    engine.invalidate_load_cache()
    engine.request_model_load()
    if not engine.request_reload(wait_timeout=120.0):
        return jsonify({
            'success': False,
            'message': 'Model load timed out after 120s. Check aimsyc_debug.log in AppData\\AimSync.',
            'model': model,
        }), 504
    status = engine.get_status_dict()
    config = load_config()
    return jsonify({
        'success': True,
        'model': model,
        'model_loaded': status.get('model_loaded'),
        'last_error': status.get('last_error', ''),
        'ai_player_class': config.get('ai_player_class', ''),
        'ai_head_class': config.get('ai_head_class', ''),
        **status,
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
    if name == 'Auto Trigger':
        config['ai_trigger_enabled'] = engine.settings.toggles[name]
        save_config(config)
    engine.settings.save_cfg(config.get('ai_active_config', 'Default.cfg'))
    experimental = is_experimental_toggle(name, engine.settings.toggles[name])
    return jsonify({
        'success': True,
        'toggle': name,
        'enabled': engine.settings.toggles[name],
        'experimental': experimental,
    })


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
        engine.request_reload()
    experimental = is_experimental_dropdown(name, value)
    return jsonify({'success': True, 'dropdown': name, 'value': value, 'experimental': experimental})


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
    value = engine.settings.sliders[name]
    experimental = is_experimental_slider(name, value)
    return jsonify({'success': True, 'slider': name, 'value': value, 'experimental': experimental})


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
    elif field == 'ai_trigger_keybind':
        config['ai_trigger_keybind'] = value
    elif field == 'ai_dynamic_fov_keybind':
        config['ai_dynamic_fov_keybind'] = value
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
    return jsonify({
        'success': True,
        'folder': folder,
        'available': [],
        'hint': COMMUNITY_STORE_MESSAGE,
        'community_store_enabled': False,
    })


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
        'baseline': {
            'sliders': BASELINE_SLIDERS,
            'toggles': BASELINE_TOGGLES,
            'dropdowns': BASELINE_DROPDOWNS,
            'aim_mode': 'normal',
        },
    })


@ai_bp.route('/config/create-default', methods=['POST'])
def ai_create_default_config():
    path = get_ai_configs_dir() / 'Default.cfg'
    if not path.is_file():
        settings = AiSettings()
        apply_default_ai_profile(settings)
        settings.save_cfg('Default.cfg')
    return jsonify({'success': True, 'configs': list_local_configs()})
