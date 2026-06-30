"""AppData AI runtime bootstrap (slim exe)."""

from __future__ import annotations

import threading

from flask import Blueprint, jsonify, request

from app.bootstrap.runtime import bootstrap_status, install_runtime
from app.core.ai_access import resolve_ai_access

bootstrap_bp = Blueprint('bootstrap', __name__, url_prefix='/api/bootstrap')

_install_thread: threading.Thread | None = None


def _run_install(*, cuda: bool) -> None:
    install_runtime(install_cuda_torch=cuda)


@bootstrap_bp.route('/status', methods=['GET'])
def status():
    return jsonify({'success': True, **bootstrap_status()})


@bootstrap_bp.route('/install', methods=['POST'])
def install():
    global _install_thread

    access = resolve_ai_access()
    if not access.get('allowed'):
        return jsonify(
            {
                'success': False,
                'error': access.get('message') or 'AI runtime install requires a supporter license',
                'ai_access': access,
            },
        ), 403

    state = bootstrap_status()
    if state['install_in_progress']:
        return jsonify({'success': False, 'error': 'Install already running'}), 409
    if state['ai_available']:
        return jsonify({'success': True, 'message': 'Already installed'})

    data = request.get_json(silent=True) or {}
    cuda = bool(data.get('cuda', True))
    _install_thread = threading.Thread(
        target=_run_install,
        kwargs={'cuda': bool(cuda)},
        name='BootstrapInstall',
        daemon=True,
    )
    _install_thread.start()
    return jsonify(
        {
            'success': True,
            'message': 'Installing AI runtime to AppData (may take 10–20 min)…',
        },
    )
