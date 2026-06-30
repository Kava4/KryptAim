"""Supporter license validation via KryptAim cloud API."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from app.core.cloud import validate_supporter_key as _cloud_validate
from app.core.env import env_get
from app.core.feedback import get_hwid

logger = logging.getLogger('KryptAim.license')

_CACHE: dict[str, Any] = {
    'key': '',
    'result': {'valid': False, 'tier': 'Free', 'display_name': '', 'message': ''},
    'fetched_at': 0.0,
}
_TTL = 300.0


def _dev_keys() -> set[str]:
    raw = env_get('KRYPTAIM_DEV_KEYS', '') or env_get('AIMSYNC_DEV_KEYS', '')
    keys = {k.strip().upper() for k in raw.split(',') if k.strip()}
    keys.add('DEV-KRYPTAIM')
    return keys


def is_dev_key(key: str) -> bool:
    return key.strip().upper() in _dev_keys()


def dev_key_result(key: str) -> dict[str, Any]:
    return {
        'valid': True,
        'tier': 'Dev',
        'display_name': 'Dev key',
        'message': '',
        'dev': True,
    }


def invalidate_license_cache() -> None:
    _CACHE['fetched_at'] = 0.0


def validate_license(key: str, *, activate_trial: bool = False, refresh: bool = False) -> dict[str, Any]:
    """Validate supporter key against cloud (HWID-bound). Dev keys work in dev only."""
    del activate_trial  # trials removed in fresh system
    normalized = (key or '').strip().upper()
    if not normalized:
        return {'valid': False, 'tier': 'Free', 'display_name': '', 'message': 'Key required'}

    if is_dev_key(normalized):
        if os.environ.get('KRYPTAIM_DEV', '').strip().lower() in {'1', 'true', 'yes', 'on'}:
            return dev_key_result(normalized)
        return {
            'valid': False,
            'tier': 'Free',
            'display_name': '',
            'message': 'Dev keys only work with run_dev.bat',
            'dev_disabled': True,
        }

    now = time.time()
    if (
        not refresh
        and _CACHE['key'] == normalized
        and now - float(_CACHE['fetched_at'] or 0) < _TTL
    ):
        return dict(_CACHE['result'])

    data, error = _cloud_validate(key=normalized, hwid=get_hwid())
    if error or not data:
        logger.warning('Cloud license validation failed: %s', error)
        result = {
            'valid': False,
            'tier': 'Free',
            'display_name': '',
            'message': error or 'Could not reach license server',
            'offline': True,
        }
    else:
        result = {
            'valid': bool(data.get('valid')),
            'tier': str(data.get('tier') or ('Supporter' if data.get('valid') else 'Free')),
            'plan': str(data.get('plan') or ('unlimited' if data.get('unlimited') else 'free')),
            'display_name': str(data.get('display_name') or ''),
            'message': str(data.get('message') or ''),
            'hwid_bound': bool(data.get('hwid_bound')),
            'unlimited': bool(data.get('unlimited')),
            'days_left': data.get('days_left'),
            'expires_at': data.get('expires_at'),
        }

    _CACHE['key'] = normalized
    _CACHE['result'] = result
    _CACHE['fetched_at'] = now
    return dict(result)


def supporter_unlock_active(key: str, *, refresh: bool = False) -> bool:
    result = validate_license(key, refresh=refresh)
    if not result.get('valid'):
        return False
    plan = str(result.get('plan') or '').lower()
    if plan == 'unlimited' or result.get('unlimited'):
        return True
    if plan == 'monthly':
        days = result.get('days_left')
        if days is None:
            return True
        try:
            return int(days) > 0
        except (TypeError, ValueError):
            return True
    return str(result.get('tier', '')).lower() != 'free'


def supporter_plan_status(key: str, *, refresh: bool = False) -> dict[str, Any]:
    result = validate_license(key, refresh=refresh)
    if not supporter_unlock_active(key, refresh=refresh):
        return {'active': False, 'plan': 'free', 'days_left': 0, 'unlimited': False}
    plan = str(result.get('plan') or 'monthly').lower()
    unlimited = bool(result.get('unlimited')) or plan == 'unlimited'
    days_left = result.get('days_left')
    try:
        days_int = int(days_left) if days_left is not None else None
    except (TypeError, ValueError):
        days_int = None
    return {
        'active': True,
        'plan': 'unlimited' if unlimited else 'monthly',
        'days_left': days_int,
        'unlimited': unlimited,
        'display_name': result.get('display_name') or '',
    }
