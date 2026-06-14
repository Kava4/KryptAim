"""Flask application for rebuild web UI."""

from __future__ import annotations

import os
import socket
import subprocess
import threading
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.serving import make_server

from app.core.config import load_config, save_config
from app.core.identity import APP_DISPLAY_NAME, APP_VERSION, APP_VERSION_LABEL
from app.core.paths import web_root
from app.recoil.weapon_data import WeaponData
from web.routes.access_routes import access_bp
from web.routes.ai_routes import ai_bp
from web.routes.bootstrap_routes import bootstrap_bp
from web.routes.projects_routes import projects_bp
from web.routes.recoil_routes import recoil_bp
from web.routes.support_routes import support_bp
from web.routes.update_routes import updates_bp

_WEB_ROOT = web_root()
_server = None
_shutdown_callback = None


def set_shutdown_callback(callback) -> None:
    global _shutdown_callback
    _shutdown_callback = callback


def get_local_ip() -> str:
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(('8.8.8.8', 80))
        ip = probe.getsockname()[0]
        probe.close()
        return ip
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return '127.0.0.1'


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(_WEB_ROOT / 'static'),
        template_folder=str(_WEB_ROOT / 'templates'),
    )
    app.register_blueprint(recoil_bp)
    app.register_blueprint(access_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(bootstrap_bp)
    app.register_blueprint(updates_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(support_bp)

    @app.context_processor
    def inject_identity():
        return {
            'app_name': APP_DISPLAY_NAME,
            'app_version': APP_VERSION,
            'app_version_label': APP_VERSION_LABEL,
            'local_ip': get_local_ip(),
        }

    @app.route('/', methods=['GET'])
    def index():
        config = load_config()
        cs2 = config.setdefault('recoil_cs2_settings', {})
        labels = WeaponData.weapon_labels()
        active_weapon = cs2.get('cs2_weapon', 'assault_rifle')
        if active_weapon not in labels:
            active_weapon = 'assault_rifle'
            cs2['cs2_weapon'] = active_weapon
        active_category = WeaponData.category_for_weapon(active_weapon)
        active_team = WeaponData.team_for_weapon(active_weapon)
        weapons_by_category = {
            cat_id: list(WeaponData.weapons_in_category(cat_id))
            for cat_id in WeaponData.CATEGORY_LABELS
        }
        weapons_by_team_category = {
            team_id: {
                cat_id: list(WeaponData.weapons_in_team_category(team_id, cat_id))
                for cat_id in WeaponData.CATEGORY_LABELS
            }
            for team_id in WeaponData.TEAM_LABELS
        }
        active_input = config.get('mouse_input_method', 'makcu')
        return render_template(
            'index.html',
            config=config,
            weapons=weapons_by_category.get(active_category, []),
            weapon_labels=labels,
            weapon_categories=WeaponData.CATEGORY_LABELS,
            weapon_teams=WeaponData.TEAM_LABELS,
            active_category=active_category,
            active_team=active_team,
            weapons_by_category=weapons_by_category,
            weapons_by_team_category=weapons_by_team_category,
            local_ip=get_local_ip(),
            active_input=active_input,
            show_integrity_check=True,
        )

    @app.route('/api/shutdown_on_exit_toggle', methods=['POST'])
    @app.route('/api/recoil/shutdown_on_exit_toggle', methods=['POST'])
    def shutdown_on_exit_toggle():
        config = load_config()
        config['shutdown_on_app_stop'] = request.form.get('shutdown_on_app_stop') == 'on'
        save_config(config)
        return '', 204

    @app.route('/api/quit', methods=['POST'])
    def quit_app():
        config = load_config()
        should_shutdown_pc = bool(config.get('shutdown_on_app_stop', False))

        def shutdown_sequence() -> None:
            import time

            time.sleep(0.4)
            try:
                from app.makcu.manager import makcu_manager

                makcu_manager.disconnect()
            except Exception:
                pass
            if _shutdown_callback is not None:
                try:
                    _shutdown_callback(should_shutdown_pc)
                    return
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

    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({'ok': True, 'build': 'rebuild'})

    return app


def run_flask() -> None:
    global _server
    app = create_app()
    _server = make_server('0.0.0.0', 5000, app)
    _server.serve_forever()


def stop_flask() -> None:
    global _server
    if _server is not None:
        try:
            _server.shutdown()
        except Exception:
            pass
        try:
            _server.server_close()
        except Exception:
            pass
        _server = None
