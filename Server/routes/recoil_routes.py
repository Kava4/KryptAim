from functools import wraps
from flask import Blueprint, render_template_string, request, make_response
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
    if method != 'software':
        return ''
    return render_template_string(
        """
        <div class="flex items-start gap-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-200/80 text-xs animate-in fade-in duration-300">
            <svg class="w-5 h-5 text-amber-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/>
            </svg>
            <p>
                <strong class="text-amber-400 block mb-0.5 uppercase tracking-wide">Security Warning</strong>
                Software input (SendInput) is significantly easier to detect. Physical hardware is highly recommended for competitive play.
            </p>
        </div>
        """
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
    connected = makcu_manager.is_connected()
    config = load_config()
    method = config.get('recoil_input_method', 'hardware')
    # Mark integrity as low if software is selected or hardware is missing
    is_unsafe = (method == 'software') or (not connected)
    integrity_level = "High (Safe)" if not is_unsafe else "Low (Unsafe)"
    integrity_color = "bg-blue-500/10 border-blue-500/50 text-blue-400" if integrity_level == "High (Safe)" else ("bg-amber-500/10 border-amber-500/50 text-amber-400" if integrity_level == "Medium" else "bg-red-500/10 border-red-500/50 text-red-400 shadow-[0_0_10px_rgba(239,68,68,0.1)]")
    dot_color = "bg-blue-500" if integrity_level == "High (Safe)" else ("bg-amber-500" if integrity_level == "Medium" else "bg-red-500")

    # This returns an HTMX component that auto-polls every 5 seconds
    return render_template_string(
        """
        <div id="hardware-status" hx-get="/api/recoil/hardware-check" hx-trigger="every 10s" hx-swap="outerHTML" class="flex flex-wrap items-center gap-3">
            <div class="flex items-center gap-2 px-3 py-1 rounded-full border transition-all duration-300 {{ 'bg-green-500/10 border-green-500/50 text-green-400 shadow-[0_0_10px_rgba(34,197,94,0.1)]' if connected else 'bg-red-500/10 border-red-500/50 text-red-400' }}">
                <div class="w-2 h-2 rounded-full {{ 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse' if connected else 'bg-red-500' }}"></div>
                <span class="text-[10px] font-bold uppercase tracking-widest">Makcu: {{ 'Connected' if connected else 'Disconnected' }}</span>
            </div>
            
            <div class="flex items-center gap-2 px-3 py-1 rounded-full border transition-all duration-300 {{ integrity_color }}">
                <div class="w-2 h-2 rounded-full {{ dot_color }} {{ 'animate-pulse' if is_unsafe else '' }}"></div>
                <span class="text-[10px] font-bold uppercase tracking-widest">Integrity: {{ integrity_level }}</span>
            </div>
        </div>
        """,
        connected=connected, is_unsafe=is_unsafe, integrity_level=integrity_level, integrity_color=integrity_color, dot_color=dot_color
    )


@recoil_bp.route('/toggle', methods=['POST'])
def toggle():
    _update_config(['recoil_enabled'], _parse_bool(request.form.get('recoil_enabled', False)))
    return '', 204


@recoil_bp.route('/keybind', methods=['POST'])
def keybind():
    _update_config(['recoil_keybind'], request.form.get('recoil_keybind', 'M4'))
    return '', 204


@recoil_bp.route('/cycle_keybind', methods=['POST'])
def cycle_keybind():
    _update_config(['recoil_cycle_keybind'], request.form.get('recoil_cycle_keybind', 'None'))
    return '', 204


@recoil_bp.route('/require_rmb', methods=['POST'])
def require_rmb():
    _update_config(['recoil_require_rmb'], _parse_bool(request.form.get('recoil_require_rmb', False)))
    return '', 204


@recoil_bp.route('/input_method', methods=['POST'])
def input_method():
    method = request.form.get('recoil_input_method', 'hardware')
    _update_config(['recoil_input_method'], method)
    return _render_input_warning(method), 200


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
    _update_config(['recoil_mode'], request.form.get('recoil_mode', 'simple'))
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
    # Delegate logic to the cloud manager module
    patterns = cloud_manager.fetch_patterns()

    return render_template_string(
        """
        {% for p in patterns %}
        <div class="flex items-center justify-between p-2 rounded-lg bg-white/5 border border-white/5 hover:border-blue-500/30 transition-all group">
            <div class="flex flex-col">
                <span class="text-xs font-semibold text-white">{{ p.name }}</span>
                <span class="text-[10px] text-white/30 uppercase tracking-tighter">by {{ p.author }}</span>
            </div>
            <button onclick="loadCloudPattern('{{ p.name }}')" class="text-[10px] font-bold text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity uppercase">Import</button>
        </div>
        {% endfor %}
        """,
        patterns=patterns
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
    if name:
        return cloud_manager.fetch_pattern_content(name), 200
    return '', 400
