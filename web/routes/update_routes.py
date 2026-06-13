"""App updates + feature flag API."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.core.feature_flags import feature_flags_status
from app.core.updates import check_for_updates, current_version, install_update

updates_bp = Blueprint('updates', __name__, url_prefix='/api/updates')


@updates_bp.route('/status', methods=['GET'])
def updates_status():
    refresh = request.args.get('refresh', '').lower() in {'1', 'true', 'yes'}
    flags = feature_flags_status(refresh=refresh)
    update_info = check_for_updates()
    return jsonify(
        {
            'success': True,
            'current_version': current_version(),
            'features': flags,
            **update_info,
        },
    )


@updates_bp.route('/check', methods=['POST', 'GET'])
def updates_check():
    refresh = True
    flags = feature_flags_status(refresh=refresh)
    update_info = check_for_updates()
    return jsonify({'success': True, 'features': flags, **update_info})


@updates_bp.route('/install', methods=['POST'])
def updates_install():
    result = install_update()
    code = 200 if result.get('success') else 400
    return jsonify(result), code
