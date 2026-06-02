import os
import sys
import threading
from pathlib import Path
import socket
import subprocess
import requests # Added for Discord Webhook

from flask import Flask, render_template, request
from werkzeug.serving import make_server

from Config.config_manager import load_config, save_config, get_pattern_names
from Config.version import APP_VERSION, APP_VERSION_LABEL
from Server import cloud_manager
from Recoil.weapon_data import WeaponData
from flask import jsonify # Ensure jsonify is imported
from Server.routes.recoil_routes import recoil_bp
from Server.routes.pattern_generator_routes import pattern_generator_bp


def resource_path(*parts: str) -> Path:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # In PyInstaller frozen mode, check if 'Server' folder exists within _MEIPASS
        # This handles both direct bundling and bundling within a 'Server' subfolder
        if (Path(sys._MEIPASS) / 'Server').is_dir():
            return Path(sys._MEIPASS).joinpath('Server', *parts)
        return Path(sys._MEIPASS, *parts) # Fallback for direct bundling
    # Source mode: app.py lives in Server/, so templates/static are relative here.
    return Path(__file__).resolve().parent.joinpath(*parts)


app = Flask(
    __name__,
    static_folder=str(resource_path('static')),
    template_folder=str(resource_path('templates')),
)

server = None

def get_local_ip():
    """Detects the local IP address on the network."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

# The remote Cloud API URL
CLOUD_API_URL = "https://project-mkgdr.vercel.app"

# List of supported games
SUPPORTED_GAMES = {
    'cs2': {'name': 'Counter-Strike 2', 'icon': 'cs2.png', 'supported': True},
    'valorant': {'name': 'Valorant', 'icon': 'valorant.png', 'supported': True},
    'pubg': {'name': 'PUBG', 'icon': 'pubg.png', 'supported': True},
    'apex': {'name': 'Apex Legends', 'icon': 'apex.png', 'supported': False},
    'cod': {'name': 'Call of Duty', 'icon': 'cod.png', 'supported': False},
    'r6s': {'name': 'Rainbow Six Siege', 'icon': 'r6s.png', 'supported': True},
    'warzone': {'name': 'Warzone', 'icon': 'warzone.png', 'supported': False},
    'delta_force': {'name': 'Delta Force', 'icon': 'delta_force.png', 'supported': False},
    'overwatch': {'name': 'Overwatch 2', 'icon': 'overwatch.png', 'supported': False},
    'the_finals': {'name': 'The Finals', 'icon': 'the_finals.png', 'supported': False},
    'battlefield': {'name': 'Battlefield', 'icon': 'battlefield.png', 'supported': False},
    'rust': {'name': 'Rust', 'icon': 'rust.png', 'supported': True}
}

app.register_blueprint(recoil_bp)
app.register_blueprint(pattern_generator_bp)


@app.context_processor
def inject_app_version():
    return {
        "app_version": APP_VERSION,
        "app_version_label": APP_VERSION_LABEL,
    }


@app.route('/', methods=['GET', 'POST'])
def index():
    config = load_config()
    # Temporary mode: all features are enabled for everyone.
    # Placeholder kept so premium logic can be restored later.
    is_premium = True
    
    # Get the data instance for the current active game
    active_game = config.get('active_game', 'cs2')
    wd = WeaponData.get_game_data(active_game)
    available_weapons = [attr for attr in dir(wd) if not attr.startswith('_') and isinstance(getattr(wd, attr), list)]
    available_weapons.sort()
    
    # If the current weapon is not in the new game's list, reset to the first available
    if config['recoil_game_settings']['weapon'] not in available_weapons:
        config['recoil_game_settings']['weapon'] = available_weapons[0] if available_weapons else 'None'
    save_config(config) # Save the potentially updated weapon

    # Render the main index page, passing the updated weapons list
    return render_template('index.html', config=config, pattern_names=get_pattern_names(),
                           local_ip=get_local_ip(), is_premium=is_premium, weapons=available_weapons, games=SUPPORTED_GAMES)


@app.route('/pattern-generator', methods=['GET'])
def pattern_generator_page():
    config = load_config()
    active_game = config.get('active_game', 'cs2')
    wd = WeaponData.get_game_data(active_game)
    available_weapons = [attr for attr in dir(wd) if not attr.startswith('_') and isinstance(getattr(wd, attr), list)]
    available_weapons.sort()
    return render_template(
        'pattern_generator.html',
        config=config,
        games=SUPPORTED_GAMES,
        weapons=available_weapons,
        active_game=active_game,
    )

@app.route('/api/recoil/toggle', methods=['POST'])
def toggle_recoil():
    """Master toggle for enabling/disabling recoil system."""
    config = load_config()
    config['recoil_enabled'] = request.form.get('recoil_enabled') == 'on'
    save_config(config)
    return '', 204

@app.route('/api/recoil/mode', methods=['POST'])
def set_recoil_mode():
    """Sets the active recoil mode (simple, advanced, CS2)."""
    config = load_config()
    config['recoil_mode'] = request.form.get('recoil_mode', 'simple')
    save_config(config)
    return '', 204

@app.route('/api/recoil/game_weapon', methods=['POST'])
def update_game_weapon():
    """Saves the selected weapon for the Game Engine."""
    config = load_config()
    weapon = request.form.get('weapon', 'assault_rifle')
    config['recoil_game_settings']['weapon'] = weapon
    save_config(config)
    return '', 204

@app.route('/api/recoil/game_sensitivity', methods=['POST'])
def update_game_sensitivity():
    """Saves the in-game sensitivity for scaling patterns."""
    config = load_config()
    sensitivity = float(request.form.get('sensitivity', 1.0))
    config['recoil_game_settings']['sensitivity'] = sensitivity
    save_config(config)
    return '', 204

@app.route('/api/recoil/game_loop', methods=['POST'])
def toggle_game_loop():
    """Toggles the loop setting for the Game Engine."""
    config = load_config()
    state = request.form.get('recoil_loop') == 'on'
    config['recoil_game_settings']['recoil_loop'] = state
    save_config(config)
    return '', 204

@app.route('/api/recoil/cycle_keybind', methods=['POST'])
def update_cycle_keybind():
    """Saves the selected mouse button for weapon cycling to the config."""
    config = load_config()
    config['recoil_cycle_keybind'] = request.form.get('recoil_cycle_keybind', 'None')
    save_config(config)
    return '', 204

@app.route('/api/recoil/active_game', methods=['POST'])
def set_active_game():
    config = load_config()
    new_game_id = request.form.get('active_game', 'cs2')
    config['active_game'] = new_game_id

    # Get the data instance for the newly selected game
    wd = WeaponData.get_game_data(new_game_id)
    available_weapons = [attr for attr in dir(wd) if not attr.startswith('_') and isinstance(getattr(wd, attr), list)]
    available_weapons.sort()

    # Reset weapon to a default for the new game if the current one doesn't exist
    if config['recoil_game_settings']['weapon'] not in available_weapons:
        config['recoil_game_settings']['weapon'] = available_weapons[0] if available_weapons else 'None'
    save_config(config)

    # Return the rendered partial template for the weapon select dropdown
    return render_template('_weapon_select.html', config=config, weapons=available_weapons, games=SUPPORTED_GAMES)

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Receives user feedback and sends it to a Discord webhook."""
    message = request.form.get('feedback_message', '').strip()
    contact = request.form.get('contact_info', '').strip()
    bug_type = request.form.get('bug_type', 'General').strip()
    hwid = cloud_manager.get_hwid() # Retrieve hardware identifier

    if not message:
        return jsonify({"success": False, "message": "Feedback message cannot be empty."}), 400

    # Prepare payload for Cloud API
    cloud_payload = {
        "message": message,
        "contact": contact,
        "type": bug_type,
        "hwid": hwid
    }
    
    try:
        # Ensure we are calling the correct cloud endpoint
        resp = requests.post(f"{CLOUD_API_URL}/api/feedback", json=cloud_payload, timeout=10)
        # Return as JSON to the frontend
        return jsonify(resp.json()), resp.status_code
    except Exception:
        return jsonify({"success": False, "message": "Cloud API unreachable."}), 502

def _render_license_status_html(data: dict, config: dict, error_override=None):
    """Placeholder for future licensing UI; currently always free."""
    return (
        '<span id="license-display" class="text-blue-400 text-[10px] font-bold '
        'uppercase tracking-widest">FREE ACCESS ENABLED</span>'
    )


@app.route('/api/recoil/license_status', methods=['GET'])
def get_license_status():
    """Placeholder endpoint for future licensing re-enable."""
    config = load_config()
    config['is_premium'] = True
    save_config(config)
    return _render_license_status_html({}, config)

@app.route('/api/recoil/validate_license', methods=['POST'])
def validate_license_local():
    """Placeholder endpoint for future licensing re-enable."""
    config = load_config()
    config['is_premium'] = True
    save_config(config)
    return _render_license_status_html({}, config)

@app.route('/api/recoil/current_weapon', methods=['GET'])
def get_current_weapon():
    """Returns the name of the currently active weapon for UI polling."""
    config = load_config()
    return config['recoil_game_settings'].get('weapon', 'None')

@app.route('/api/recoil/shutdown_on_exit_toggle', methods=['POST'])
def shutdown_on_exit_toggle():
    """Toggles the auto-shutdown on app exit setting."""
    config = load_config()
    config['shutdown_on_app_stop'] = request.form.get('shutdown_on_app_stop') == 'on'
    save_config(config)
    return '', 204

@app.route('/api/recoil/safety_features_toggle', methods=['POST'])
def safety_features_toggle():
    """Toggles the global safety features on or off."""
    config = load_config()
    state = request.form.get('recoil_safety_features_enabled') == 'on'
    config['recoil_safety_features_enabled'] = state
    save_config(config)
    return '', 204


@app.route('/api/quit', methods=['POST'])
def quit_app():
    """Triggers a clean exit of the entire application."""
    config = load_config()
    should_shutdown_pc = config.get('shutdown_on_app_stop', False)
    
    def shutdown_sequence():
        import time
        # Small delay to allow the 204 response to be sent back to the browser
        time.sleep(0.5)
        # Attempt to release hardware before killing the process
        try:
            from Makcu.makcu_manager import makcu_manager
            makcu_manager.disconnect()
        except Exception:
            pass
            
        if should_shutdown_pc:
            try:
                subprocess.run(['shutdown', '/s', '/t', '0'], check=True)
            except Exception:
                pass

        os._exit(0)

    threading.Thread(target=shutdown_sequence, daemon=True).start()
    return '', 204


@app.route('/api/shutdown_computer', methods=['POST'])
def shutdown_computer():
    """Triggers a system shutdown."""
    def system_shutdown_sequence():
        import time
        # Give the browser a moment to process the response before shutting down
        time.sleep(1) 
        try:
            # This command is for Windows. For other OS, it would be different.
            # Ensure the user running the app has permissions to shut down.
            subprocess.run(['shutdown', '/s', '/t', '0'], check=True)
        except Exception as e:
            print(f"Error initiating system shutdown: {e}")
            # In a real scenario, you might want to log this error more persistently.
        os._exit(0) # Ensure the app exits even if shutdown command fails for some reason

    threading.Thread(target=system_shutdown_sequence, daemon=True).start()
    return '', 204 # Return success to the browser immediately

def run_flask():
    global server
    server = make_server('0.0.0.0', 5000, app)
    server.serve_forever()


def stop_flask():
    global server
    if server is not None:
        try:
            server.shutdown()
        except Exception:
            pass
        try:
            server.server_close()
        except Exception:
            pass
        server = None