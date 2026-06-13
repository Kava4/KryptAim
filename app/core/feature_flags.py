"""Remote + local feature flags (AI premium gate, etc.)."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from app.core.github import get_json, raw_github_url

logger = logging.getLogger('AimSync.features')

_ON = frozenset({'1', 'true', 'yes', 'on'})
_REMOTE_TTL = 300.0
_REMOTE_CACHE: dict[str, Any] = {'data': {}, 'fetched_at': 0.0, 'error': None}

DEFAULT_REPO = os.environ.get('AIMSYNC_UPDATES_REPO', 'AimSyncCore/AimSync')
DEFAULT_REF = os.environ.get('AIMSYNC_APP_CONFIG_REF', 'main')
DEFAULT_CONFIG_PATH = os.environ.get('AIMSYNC_APP_CONFIG_PATH', 'release/app-config.json')


def _env_on(name: str) -> bool:
    return os.environ.get(name, '').strip().lower() in _ON


def _config_url() -> str:
    custom = os.environ.get('AIMSYNC_APP_CONFIG_URL', '').strip()
    if custom:
        return custom
    return raw_github_url(DEFAULT_REPO, DEFAULT_REF, DEFAULT_CONFIG_PATH)


def invalidate_remote_config_cache() -> None:
    _REMOTE_CACHE['fetched_at'] = 0.0


def fetch_remote_config(*, force: bool = False) -> dict[str, Any]:
    now = time.time()
    if (
        not force
        and _REMOTE_CACHE['data']
        and now - float(_REMOTE_CACHE['fetched_at'] or 0) < _REMOTE_TTL
    ):
        return dict(_REMOTE_CACHE['data'])

    data, err = get_json(_config_url())
    if err or not isinstance(data, dict):
        logger.debug('Remote app-config unavailable: %s', err)
        _REMOTE_CACHE['error'] = err
        if _REMOTE_CACHE['data']:
            return dict(_REMOTE_CACHE['data'])
        return {}

    _REMOTE_CACHE['data'] = data
    _REMOTE_CACHE['fetched_at'] = now
    _REMOTE_CACHE['error'] = None
    return dict(data)


def ai_premium_required(*, refresh: bool = False) -> bool:
    """When False (default), AI is free. Lock later via env or release/app-config.json."""
    if _env_on('AIMSYNC_AI_PREMIUM_ONLY'):
        return True
    if _env_on('AIMSYNC_AI_FREE'):
        return False

    remote = fetch_remote_config(force=refresh)
    if 'ai_premium_only' in remote:
        return bool(remote['ai_premium_only'])
    return False


def feature_flags_status(*, refresh: bool = False) -> dict[str, Any]:
    remote = fetch_remote_config(force=refresh)
    premium = ai_premium_required(refresh=refresh)
    return {
        'ai_premium_only': premium,
        'ai_free': not premium,
        'remote_config': remote,
        'remote_error': _REMOTE_CACHE.get('error'),
        'config_url': _config_url(),
    }
