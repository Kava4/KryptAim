"""License validation and AI access status."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.core.config import load_config, save_config
from app.core.ai_access import invalidate_ai_access_cache, resolve_ai_access
from app.core.license_cloud import validate_license

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
    status = resolve_ai_access(refresh=refresh)
    return jsonify({'success': True, **status})


@access_bp.route('/validate_license', methods=['POST'])
def access_validate_license():
    key = _license_key_from_request()
    result = validate_license(key, refresh=True)
    config = load_config()
    if key:
        config['license_key'] = key
    config['is_premium'] = bool(result.get('valid'))
    save_config(config)
    invalidate_ai_access_cache()

    status = resolve_ai_access(refresh=True)
    return jsonify({'success': True, 'license': result, **status})
