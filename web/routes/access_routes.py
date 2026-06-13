"""License validation and AI access status."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.core.config import load_config, save_config
from app.core.licensing import ai_access_status, invalidate_license_cache, validate_license

access_bp = Blueprint('access', __name__, url_prefix='/api/access')


def _license_key_from_request() -> str:
    data = request.get_json(silent=True) or {}
    return str(
        request.form.get('license_key')
        or data.get('license_key')
        or data.get('key')
        or '',
    ).strip()


@access_bp.route('/status', methods=['GET'])
def access_status():
    refresh = request.args.get('refresh', '').lower() in {'1', 'true', 'yes'}
    status = ai_access_status(refresh=refresh)
    return jsonify({'success': True, **status})


@access_bp.route('/validate_license', methods=['POST'])
def access_validate_license():
    key = _license_key_from_request()
    activate_trial = str(
        request.form.get('activate_trial') or (request.get_json(silent=True) or {}).get('activate_trial') or '',
    ).lower() in {'1', 'true', 'on', 'yes'}

    result = validate_license(key, activate_trial=activate_trial)
    config = load_config()
    if key:
        config['license_key'] = key
    config['is_premium'] = bool(result.get('valid'))
    save_config(config)
    invalidate_license_cache()

    status = ai_access_status(refresh=True)
    return jsonify({'success': True, 'license': result, **status})
