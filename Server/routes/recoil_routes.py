import json
from functools import wraps
from flask import Blueprint, render_template_string, request, make_response, jsonify
from Input.methods import method_display_name, resolve_mouse_input_method, sync_legacy_recoil_input_method, use_alt_input
from Input.router import input_router
from Makcu.makcu_manager import makcu_manager
from Server import cloud_manager

from Config.config_manager import (
    delete_pattern_file,
    get_pattern_names,
    load_config,
    load_pattern_file,
    save_config,
    save_pattern_file,
)
from Recoil.hotkeys import (
    HotkeyValidationError,
    normalize_hotkey_string,
    set_hotkey_binding_active,
    validate_hotkey_bindings,
)
from Recoil.recoil import reset_master_toggle_hotkey

recoil_bp = Blueprint('recoil_bp', __name__, url_prefix='/api/recoil')

def _parse_bool(value):
    return str(value).lower() in {'1', 'true', 'on', 'yes'}


def _parse_number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _update_config(path, value):
    config = load_config()
    current = config
    for key in path[:-1]:
        current = current.setdefault(key, {})
    current[path[-1]] = value
    save_config(config)
    return config

def donator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Placeholder gate: temporarily bypassed while app is fully free.
        # Keep decorator so premium checks can be re-enabled later.
        return f(*args, **kwargs)
    return decorated_function

def _render_pattern_select(config):
    return render_template_string(
        """
        <option value="">...</option>
        {% for name in pattern_names %}
        <option value="{{ name }}" {{ 'selected' if config.recoil_advanced_settings.recoil_active_pattern_name == name else '' }}>{{ name }}</option>
        {% endfor %}
        """,
        config=config,
        pattern_names=get_pattern_names(),
    )


def _render_input_warning(method):
    key = (method or '').strip().lower()
    if key in ('hardware', 'makcu'):
        return ''
    label = method_display_name(resolve_mouse_input_method({'mouse_input_method': key}))
    if key == 'software':
        label = method_display_name('win32')
    return render_template_string(
        """
        <div class="flex items-start gap-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-200/80 text-xs animate-in fade-in duration-300">
            <svg class="w-5 h-5 text-amber-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/>
            </svg>
            <p>
                <strong class="text-amber-400 block mb-0.5 uppercase tracking-wide">Dual-PC / local input warning</strong>
                {{ label }} moves and clicks on <em>this</em> PC only. For gaming-PC control via Makcu, select <strong>Hardware (Makcu)</strong>.
            </p>
        </div>
        """,
        label=label,
    )


def _render_license_status(data):
    if not isinstance(data, dict):
        is_valid = data
        days_left = None
        name = None
    else:
        is_valid = data.get('valid', False)
        days_left = data.get('days_left')
        name = data.get('display_name')

    if is_valid:
        status_text = f"Supporter: {name}" if name else "Premium Active"
        if days_left is not None:
            status_text += f" ({days_left}d left)"
        return f'<span class="text-[10px] font-bold text-blue-400 bg-blue-400/10 border border-blue-400/20 px-2 py-0.5 rounded-full uppercase tracking-tighter shadow-[0_0_10px_rgba(96,165,250,0.1)]">{status_text}</span>'
    return '<span class="text-[10px] font-bold text-white/20 bg-white/5 border border-white/10 px-2 py-0.5 rounded-full uppercase tracking-tighter">Free Version</span>'


@recoil_bp.route('/status', methods=['GET'])
def status():
    config = load_config()
    return render_template_string(
        """
        <input id="recoil-toggle" type="checkbox" name="recoil_enabled"
               class="w-4 h-4 accent-blue-500 cursor-pointer"
               {{ 'checked' if config.recoil_enabled else '' }}
               onchange="fetch('/api/recoil/toggle', {method:'POST', body: new URLSearchParams({recoil_enabled: this.checked ? 'on' : 'off'})})">
        """,
        config=config,
    )

@recoil_bp.route('/hardware-check', methods=['GET'])
def hardware_check():
    """Endpoint for the UI to verify hardware connection status."""
    config = load_config()
    method = resolve_mouse_input_method(config)

    if method == 'makcu':
        if not makcu_manager.is_connected():
            makcu_manager.connect()
        hardware = makcu_manager.is_hardware()
        connected = hardware and makcu_manager.is_connected()
        is_unsafe = not connected
        input_label = 'Makcu'
        if connected:
            input_status = 'Connected'
            input_style = 'bg-green-500/10 border-green-500/50 text-green-400 shadow-[0_0_10px_rgba(34,197,94,0.1)]'
            input_dot = 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse'
        elif hardware:
            input_status = 'Disconnected'
            input_style = 'bg-red-500/10 border-red-500/50 text-red-400'
            input_dot = 'bg-red-500'
        else:
            input_status = 'Not connected'
            input_style = 'bg-red-500/10 border-red-500/50 text-red-400'
            input_dot = 'bg-red-500'
    else:
        status = input_router.status(config)
        input_label = status.get('method_label', method_display_name(method))
        connected = bool(status.get('connected'))
        is_unsafe = True
        if connected:
            input_status = 'Connected'
            input_style = 'bg-green-500/10 border-green-500/50 text-green-400 shadow-[0_0_10px_rgba(34,197,94,0.1)]'
            input_dot = 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse'
        else:
            input_status = status.get('last_error') or 'Not connected'
            input_style = 'bg-red-500/10 border-red-500/50 text-red-400'
            input_dot = 'bg-red-500'

    integrity_level = "High (Safe)" if not is_unsafe else "Low (Unsafe)"
    integrity_color = "bg-blue-500/10 border-blue-500/50 text-blue-400" if integrity_level == "High (Safe)" else ("bg-amber-500/10 border-amber-500/50 text-amber-400" if integrity_level == "Medium" else "bg-red-500/10 border-red-500/50 text-red-400 shadow-[0_0_10px_rgba(239,68,68,0.1)]")
    dot_color = "bg-blue-500" if integrity_level == "High (Safe)" else ("bg-amber-500" if integrity_level == "Medium" else "bg-red-500")

    return render_template_string(
        """
        <div id="hardware-status" hx-get="/api/recoil/hardware-check" hx-trigger="every 10s" hx-swap="outerHTML" class="flex flex-wrap items-center gap-3">
            <div class="flex items-center gap-2 px-3 py-1 rounded-full border transition-all duration-300 {{ input_style }}">
                <div class="w-2 h-2 rounded-full {{ input_dot }}"></div>
                <span class="text-[10px] font-bold uppercase tracking-widest">{{ input_label }}: {{ input_status }}</span>
            </div>
            
            <div class="flex items-center gap-2 px-3 py-1 rounded-full border transition-all duration-300 {{ integrity_color }}">
                <div class="w-2 h-2 rounded-full {{ dot_color }} {{ 'animate-pulse' if is_unsafe else '' }}"></div>
                <span class="text-[10px] font-bold uppercase tracking-widest">Integrity: {{ integrity_level }}</span>
            </div>
        </div>
        """,
        input_label=input_label,
        input_status=input_status,
        input_style=input_style,
        input_dot=input_dot,
        is_unsafe=is_unsafe,
        integrity_level=integrity_level,
        integrity_color=integrity_color,
        dot_color=dot_color,
    )


@recoil_bp.route('/toggle', methods=['POST'])
def toggle():
    _update_config(['recoil_enabled'], _parse_bool(request.form.get('recoil_enabled', False)))
    reset_master_toggle_hotkey()
    return '', 204


@recoil_bp.route('/hotkey-binding', methods=['POST'])
def hotkey_binding():
    set_hotkey_binding_active(_parse_bool(request.form.get('active', False)))
    return '', 204


def _validate_all_hotkeys(config: dict) -> None:
    validate_hotkey_bindings(
        config.get('global_toggle_hotkey') or config.get('recoil_keybind'),
        config.get('weapon_cycle_hotkey') or config.get('recoil_cycle_keybind'),
        config.get('weapon_direct_binds'),
        ai_aim_keybind=config.get('ai_aim_keybind'),
        ai_second_aim_keybind=config.get('ai_second_aim_keybind'),
        ai_engine_toggle_hotkey=config.get('ai_engine_toggle_hotkey'),
    )


def _apply_hotkey_field(config: dict, field: str, normalized: str) -> None:
    ai_fields = {'ai_aim_keybind', 'ai_second_aim_keybind', 'ai_engine_toggle_hotkey'}

    if field in {'recoil_keybind', 'global_toggle_hotkey'}:
        config['recoil_keybind'] = normalized
        config['global_toggle_hotkey'] = normalized
    elif field in {'recoil_cycle_keybind', 'weapon_cycle_hotkey'}:
        config['recoil_cycle_keybind'] = normalized
        config['weapon_cycle_hotkey'] = normalized
    elif field in ai_fields:
        config[field] = normalized
    else:
        raise HotkeyValidationError(f'Unknown hotkey field "{field}".')

    _validate_all_hotkeys(config)


@recoil_bp.route('/hotkey', methods=['POST'])
def set_hotkey():
    field = (request.form.get('field') or '').strip()
    raw_value = request.form.get('value', 'None')
    config = load_config()
    try:
        normalized = normalize_hotkey_string(raw_value)
        _apply_hotkey_field(config, field, normalized)
    except HotkeyValidationError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    save_config(config)
    if field in {'recoil_keybind', 'global_toggle_hotkey'}:
        reset_master_toggle_hotkey()
    return jsonify({'success': True, 'field': field, 'value': normalized})


@recoil_bp.route('/keybind', methods=['POST'])
def keybind():
    try:
        normalized = normalize_hotkey_string(request.form.get('recoil_keybind', 'M4'))
        config = load_config()
        _apply_hotkey_field(config, 'recoil_keybind', normalized)
    except HotkeyValidationError as exc:
        return str(exc), 400
    save_config(config)
    return '', 204


@recoil_bp.route('/cycle_keybind', methods=['POST'])
def cycle_keybind():
    hotkey_value = request.form.get('recoil_cycle_keybind', 'None')
    try:
        normalized = normalize_hotkey_string(hotkey_value)
        config = load_config()
        _apply_hotkey_field(config, 'recoil_cycle_keybind', normalized)
    except HotkeyValidationError as exc:
        return str(exc), 400
    save_config(config)
    return '', 204


@recoil_bp.route('/hotkeys', methods=['POST'])
def hotkeys():
    config = load_config()
    global_toggle = request.form.get('global_toggle_hotkey', config.get('global_toggle_hotkey', 'M4'))
    cycle_hotkey = request.form.get('weapon_cycle_hotkey', config.get('weapon_cycle_hotkey', 'None'))
    ai_aim = request.form.get('ai_aim_keybind', config.get('ai_aim_keybind', 'rmb'))
    ai_second = request.form.get('ai_second_aim_keybind', config.get('ai_second_aim_keybind', 'alt'))
    ai_toggle = request.form.get('ai_engine_toggle_hotkey', config.get('ai_engine_toggle_hotkey', 'None'))

    raw_direct_binds = request.form.get('weapon_direct_binds', '')
    direct_binds = config.get('weapon_direct_binds', {})
    if raw_direct_binds:
        try:
            parsed = json.loads(raw_direct_binds)
        except json.JSONDecodeError:
            return jsonify({'success': False, 'message': 'Weapon binds must be valid JSON.'}), 400

        direct_binds = {}
        for item in parsed:
            hotkey_value = str(item.get('hotkey', '')).strip()
            weapon = str(item.get('weapon', '')).strip()
            if hotkey_value and weapon:
                direct_binds[normalize_hotkey_string(hotkey_value)] = weapon

    try:
        global_toggle = normalize_hotkey_string(global_toggle)
        cycle_hotkey = normalize_hotkey_string(cycle_hotkey)
        ai_aim = normalize_hotkey_string(ai_aim)
        ai_second = normalize_hotkey_string(ai_second)
        ai_toggle = normalize_hotkey_string(ai_toggle)
        validate_hotkey_bindings(
            global_toggle,
            cycle_hotkey,
            direct_binds,
            ai_aim_keybind=ai_aim,
            ai_second_aim_keybind=ai_second,
            ai_engine_toggle_hotkey=ai_toggle,
        )
    except HotkeyValidationError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400

    config['global_toggle_hotkey'] = global_toggle
    config['recoil_keybind'] = global_toggle
    config['weapon_cycle_hotkey'] = cycle_hotkey
    config['recoil_cycle_keybind'] = cycle_hotkey
    config['weapon_direct_binds'] = direct_binds
    config['ai_aim_keybind'] = ai_aim
    config['ai_second_aim_keybind'] = ai_second
    config['ai_engine_toggle_hotkey'] = ai_toggle
    save_config(config)
    return jsonify({
        'success': True,
        'global_toggle_hotkey': global_toggle,
        'weapon_cycle_hotkey': cycle_hotkey,
        'weapon_direct_binds': direct_binds,
        'ai_aim_keybind': ai_aim,
        'ai_second_aim_keybind': ai_second,
        'ai_engine_toggle_hotkey': ai_toggle,
    })


@recoil_bp.route('/hotkeys/validate', methods=['POST'])
def validate_hotkeys_route():
    payload = request.get_json(silent=True) or {}
    try:
        global_toggle = normalize_hotkey_string(payload.get('global_toggle_hotkey'))
        cycle_hotkey = normalize_hotkey_string(payload.get('weapon_cycle_hotkey'))
        direct_binds = {
            normalize_hotkey_string(entry.get('hotkey')): str(entry.get('weapon', '')).strip()
            for entry in payload.get('weapon_direct_binds', [])
            if str(entry.get('hotkey', '')).strip() and str(entry.get('weapon', '')).strip()
        }
        ai_aim = normalize_hotkey_string(payload.get('ai_aim_keybind'))
        ai_second = normalize_hotkey_string(payload.get('ai_second_aim_keybind'))
        ai_toggle = normalize_hotkey_string(payload.get('ai_engine_toggle_hotkey'))
        validate_hotkey_bindings(
            global_toggle,
            cycle_hotkey,
            direct_binds,
            ai_aim_keybind=ai_aim,
            ai_second_aim_keybind=ai_second,
            ai_engine_toggle_hotkey=ai_toggle,
        )
        return jsonify({
            'success': True,
            'global_toggle_hotkey': global_toggle,
            'weapon_cycle_hotkey': cycle_hotkey,
            'weapon_direct_binds': direct_binds,
            'ai_aim_keybind': ai_aim,
            'ai_second_aim_keybind': ai_second,
            'ai_engine_toggle_hotkey': ai_toggle,
        })
    except HotkeyValidationError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400


@recoil_bp.route('/require_rmb', methods=['POST'])
def require_rmb():
    _update_config(['recoil_require_rmb'], _parse_bool(request.form.get('recoil_require_rmb', False)))
    return '', 204


@recoil_bp.route('/input_method', methods=['POST'])
def input_method():
    method = request.form.get('recoil_input_method', 'hardware')
    config = load_config()
    legacy_map = {
        'hardware': 'makcu',
        'software': 'win32',
    }
    if method in legacy_map:
        config['mouse_input_method'] = legacy_map[method]
    else:
        config['mouse_input_method'] = method.strip().lower()
    sync_legacy_recoil_input_method(config)
    save_config(config)
    if use_alt_input(config):
        input_router.reload(config)
    return _render_input_warning(method), 200


@recoil_bp.route('/alt_input_settings', methods=['POST'])
def alt_input_settings():
    config = load_config()
    for key in (
        'arduino_port',
        'ghub_dll_path',
        'razer_dll_path',
        'kmbox_net_ip',
        'kmbox_net_port',
        'kmbox_net_uuid',
    ):
        if key in request.form:
            config[key] = request.form.get(key, '')
    save_config(config)
    if use_alt_input(config):
        input_router.reload(config)
    return '', 204


@recoil_bp.route('/randomisation', methods=['POST'])
def randomisation():
    _update_config(['recoil_randomisation'], _parse_bool(request.form.get('recoil_randomisation', False)))
    return '', 204


@recoil_bp.route('/random_strength', methods=['POST'])
def random_strength():
    _update_config(['recoil_random_strength'], _parse_number(request.form.get('recoil_random_strength', 5.0), 5.0))
    return '', 204


@recoil_bp.route('/x_control', methods=['POST'])
def x_control():
    _update_config(['recoil_x_control'], _parse_number(request.form.get('recoil_x_control', 100), 100))
    return '', 204


@recoil_bp.route('/speed_control', methods=['POST'])
def speed_control():
    _update_config(['recoil_speed_control'], _parse_number(request.form.get('recoil_speed_control', 100), 100))
    return '', 204


@recoil_bp.route('/y_control', methods=['POST'])
def y_control():
    _update_config(['recoil_y_control'], _parse_number(request.form.get('recoil_y_control', 100), 100))
    return '', 204


@recoil_bp.route('/x', methods=['POST'])
def x_setting():
    _update_config(['recoil_simple_settings', 'recoil_x'], _parse_number(request.form.get('x', 0), 0))
    return '', 204


@recoil_bp.route('/y', methods=['POST'])
def y_setting():
    _update_config(['recoil_simple_settings', 'recoil_y'], _parse_number(request.form.get('y', 0), 0))
    return '', 204


@recoil_bp.route('/delay', methods=['POST'])
def delay_setting():
    _update_config(['recoil_simple_settings', 'recoil_delay'], _parse_number(request.form.get('recoil_delay', 50), 50))
    return '', 204


SIMPLE_RECOIL_DEFAULTS = {
    'recoil_x': 0,
    'recoil_y': 0,
    'recoil_delay': 50,
}


@recoil_bp.route('/simple/reset', methods=['POST'])
def reset_simple_recoil():
    config = load_config()
    config['recoil_simple_settings'] = dict(SIMPLE_RECOIL_DEFAULTS)
    save_config(config)
    return jsonify({'success': True, **config['recoil_simple_settings']})


@recoil_bp.route('/advanced_pattern', methods=['POST'])
def advanced_pattern():
    raw_pattern = request.form.get('advanced_pattern', '')
    steps = []
    for line in raw_pattern.splitlines():
        parts = [item.strip() for item in line.split(',') if item.strip()]
        if len(parts) >= 3:
            try:
                steps.append({
                    'x': _parse_number(parts[0]),
                    'y': _parse_number(parts[1]),
                    'delay_ms': int(_parse_number(parts[2])),
                })
            except ValueError:
                continue
    _update_config(['recoil_advanced_settings', 'recoil_selected_pattern'], steps)
    return '', 204


@recoil_bp.route('/loop', methods=['POST'])
def loop_setting():
    _update_config(['recoil_advanced_settings', 'recoil_loop'], _parse_bool(request.form.get('recoil_loop', False)))
    return '', 204


@recoil_bp.route('/cs2_weapon', methods=['GET'])
def get_cs2_weapon():
    """Get the current CS2 weapon setting (used for hotkey cycling updates)."""
    config = load_config()
    weapon = config.get('recoil_cs2_settings', {}).get('cs2_weapon', 'assault_rifle')
    return weapon, 200

@recoil_bp.route('/cs2_weapon', methods=['POST'])
def cs2_weapon():
    _update_config(['recoil_cs2_settings', 'cs2_weapon'], request.form.get('cs2_weapon', 'assault_rifle'))
    return '', 204


@recoil_bp.route('/cs2_sensitivity', methods=['POST'])
def cs2_sensitivity():
    _update_config(['recoil_cs2_settings', 'cs2_sensitivity'], _parse_number(request.form.get('cs2_sensitivity', 1.0), 1.0))
    return '', 204


@recoil_bp.route('/mode', methods=['POST'])
def mode():
    from Recoil.recoil import reset_pattern_state

    new_mode = request.form.get('recoil_mode', 'simple')
    config = load_config()
    if config.get('recoil_mode') != new_mode:
        config['recoil_mode'] = new_mode
        save_config(config)
        reset_pattern_state()
    return '', 204


@recoil_bp.route('/pattern/save', methods=['POST'])
def save_pattern():
    name = request.form.get('pattern_name', '').strip()
    raw_pattern = request.form.get('advanced_pattern', '')
    if name:
        save_pattern_file(name, raw_pattern)
    return _render_pattern_select(load_config()), 200


@recoil_bp.route('/pattern/load', methods=['POST'])
def load_pattern():
    name = request.form.get('pattern_name', '').strip()
    if name:
        pattern = load_pattern_file(name)
        return '\n'.join(f"{step.get('x', 0)},{step.get('y', 0)},{step.get('delay_ms', 0)}" for step in pattern), 200
    return '', 204


@recoil_bp.route('/pattern/delete', methods=['POST'])
def delete_pattern():
    name = request.form.get('pattern_name', '').strip()
    if name:
        delete_pattern_file(name)
    return _render_pattern_select(load_config()), 200


@recoil_bp.route('/cloud/list', methods=['GET'])
def cloud_list():
    """Fetches a list of public patterns from the remote server."""
    result = cloud_manager.fetch_patterns()
    patterns = result.get('patterns', [])
    online = result.get('online', False)
    error = result.get('error')

    return render_template_string(
        """
        {% if error %}
        <div class="col-span-2 rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2 text-[11px] text-amber-200/90">
            Cloud unreachable — check internet on AimSync PC. ({{ error }})
        </div>
        {% elif not patterns %}
        <div class="col-span-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-[11px] text-white/45">
            Repository online — no community patterns yet. Use <strong class="text-white/70">Share</strong> to upload the first one.
        </div>
        {% else %}
        {% for p in patterns %}
        <div class="flex items-center justify-between p-2 rounded-lg bg-white/5 border border-white/5 hover:border-blue-500/30 transition-all group">
            <div class="flex flex-col min-w-0">
                <span class="text-xs font-semibold text-white truncate">{{ p.name }}</span>
                <span class="text-[10px] text-white/30 uppercase tracking-tighter">by {{ p.author }}</span>
            </div>
            <button type="button" data-cloud-name="{{ p.name | e }}" class="cloud-import-btn text-[10px] font-bold text-blue-400 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity uppercase shrink-0 ml-2">Import</button>
        </div>
        {% endfor %}
        {% endif %}
        """,
        patterns=patterns,
        online=online,
        error=error,
    )

@recoil_bp.route('/cloud/upload', methods=['POST'])
def cloud_upload():
    """Uploads the current local pattern to the cloud repository."""
    config = load_config()
    author = config.get('cloud_username', 'Anonymous')
    name = request.form.get('pattern_name', '').strip()
    content = request.form.get('advanced_pattern', '')
    
    # Delegate upload logic to the cloud manager module
    success, message = cloud_manager.upload_pattern(name, content, author)
    return message, (200 if success else 400)

@recoil_bp.route('/cloud_username', methods=['POST'])
def cloud_username():
    _update_config(['cloud_username'], request.form.get('cloud_username', 'Anonymous'))
    return '', 204

# License routes live in Server/app.py (trial activation + cloud proxy).
# Do not register them here — duplicate routes shadow app.py and break free trial.

@recoil_bp.route('/cloud/load', methods=['GET'])
def cloud_load():
    """Retrieves content from the cloud to inject into the local editor."""
    name = request.args.get('name', '').strip()
    if not name:
        return 'Missing pattern name.', 400
    content = cloud_manager.fetch_pattern_content(name)
    if not content or not content.strip():
        return f'Pattern "{name}" not found or empty on cloud.', 404
    return content, 200
