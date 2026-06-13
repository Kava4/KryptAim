"""License validation and donor-only AI access."""

from __future__ import annotations

import logging
import os
import sys
import time
import uuid
from typing import Any

from app.core.cloud import _post_json
from app.core.config import load_config
from app.core.feature_flags import ai_premium_required
from app.core.runtime import dev_mode_enabled

logger = logging.getLogger('AimSync.licensing')

_VERIFY_INTERVAL = 300.0
FREE_TRIAL_KEYS = frozenset({'', 'FREE', 'EARLY', 'FREETRIAL', 'TRIAL'})
DEV_KEY_PREFIXES = ('DEV-', 'AIMSYNC-DEV-')
DEFAULT_DEV_KEY = 'DEV-AIMSYNC'

_CACHE: dict[str, Any] = {
    'valid': False,
    'tier': 'Free',
    'display_name': None,
    'remaining_seconds': None,
    'days_left': None,
    'trial_available': False,
    'last_check': 0.0,
    'last_key': '',
}


def get_hwid() -> str:
    return str(uuid.getnode())


def sync_license_cache(data: dict[str, Any]) -> None:
    _CACHE['valid'] = bool(data.get('valid'))
    _CACHE['tier'] = str(data.get('tier') or 'Free')
    _CACHE['display_name'] = data.get('display_name')
    _CACHE['remaining_seconds'] = data.get('remaining_seconds')
    _CACHE['days_left'] = data.get('days_left')
    _CACHE['trial_available'] = bool(data.get('trial_available'))
    _CACHE['last_check'] = time.time()


def invalidate_license_cache() -> None:
    _CACHE['last_check'] = 0.0


def dev_ai_unlocked() -> bool:
    return os.environ.get('AIMSYNC_AI_UNLOCK', '').strip().lower() in {'1', 'true', 'yes', 'on'}


def dev_keys_enabled() -> bool:
    """Dev license keys work in source runs, --dev, or when explicitly allowed."""
    if dev_ai_unlocked() or dev_mode_enabled():
        return True
    if os.environ.get('AIMSYNC_ALLOW_DEV_KEYS', '').strip().lower() in {'1', 'true', 'yes', 'on'}:
        return True
    return not getattr(sys, 'frozen', False)


def _extra_dev_keys() -> set[str]:
    raw = os.environ.get('AIMSYNC_DEV_KEYS', '')
    keys = {part.strip().upper() for part in raw.split(',') if part.strip()}
    keys.add(DEFAULT_DEV_KEY)
    return keys


def is_dev_license_key(key: str) -> bool:
    normalized = (key or '').strip().upper()
    if not normalized:
        return False
    if normalized in _extra_dev_keys():
        return True
    return any(normalized.startswith(prefix) for prefix in DEV_KEY_PREFIXES)


def _dev_license_result(key: str) -> dict[str, Any]:
    label = (key or '').strip() or DEFAULT_DEV_KEY
    return {
        'valid': True,
        'tier': 'Dev',
        'display_name': f'Dev key ({label})',
        'days_left': None,
        'remaining_seconds': None,
        'trial_available': False,
        'dev': True,
    }


def is_trial_license(key: str, data: dict[str, Any]) -> bool:
    if data.get('dev') or str(data.get('tier', '')).lower() == 'dev':
        return False
    normalized = (key or '').strip().upper()
    if normalized in FREE_TRIAL_KEYS:
        return True
    if normalized.startswith('TRIAL_'):
        return True
    display = str(data.get('display_name') or '').lower()
    if 'free trial' in display:
        return True
    if data.get('trial_available') and not normalized:
        return True
    return False


def ai_access_allowed(data: dict[str, Any], key: str) -> bool:
    if dev_ai_unlocked():
        return True
    if data.get('dev') or str(data.get('tier', '')).lower() == 'dev':
        return dev_keys_enabled()
    if not data.get('valid'):
        return False
    if is_trial_license(key, data):
        return False
    tier = str(data.get('tier') or '').lower()
    if tier in {'free', 'banned', 'revoked'}:
        return False
    normalized = (key or '').strip().upper()
    if normalized in FREE_TRIAL_KEYS:
        return False
    return True


def validate_license(key: str, *, activate_trial: bool = False) -> dict[str, Any]:
    normalized = (key or '').strip()
    if dev_keys_enabled() and is_dev_license_key(normalized):
        result = _dev_license_result(normalized)
        sync_license_cache(result)
        _CACHE['last_key'] = normalized
        return result

    payload = {
        'key': normalized,
        'hwid': get_hwid(),
        'activate_trial': bool(activate_trial),
    }
    data, error = _post_json('license/validate', payload, timeout=8)
    if error or not isinstance(data, dict):
        logger.warning('License validation failed: %s', error)
        result = {'valid': False, 'tier': 'Free', 'error': error or 'Cloud unreachable'}
        sync_license_cache(result)
        return result
    sync_license_cache(data)
    _CACHE['last_key'] = normalized
    return data


def _refresh_if_stale(key: str) -> dict[str, Any]:
    now = time.time()
    normalized = (key or '').strip()
    stale = now - float(_CACHE.get('last_check') or 0) > _VERIFY_INTERVAL
    key_changed = normalized != str(_CACHE.get('last_key') or '')
    if stale or key_changed or not _CACHE.get('last_check'):
        return validate_license(normalized, activate_trial=False)
    return {
        'valid': bool(_CACHE.get('valid')),
        'tier': _CACHE.get('tier', 'Free'),
        'display_name': _CACHE.get('display_name'),
        'remaining_seconds': _CACHE.get('remaining_seconds'),
        'days_left': _CACHE.get('days_left'),
        'trial_available': bool(_CACHE.get('trial_available')),
    }


def ai_access_status(*, refresh: bool = False) -> dict[str, Any]:
    config = load_config()
    key = str(config.get('license_key') or '').strip()
    premium_required = ai_premium_required(refresh=refresh)

    if dev_ai_unlocked():
        return {
            'allowed': True,
            'tier': 'Dev',
            'display_name': 'Developer unlock',
            'message': '',
            'license_valid': True,
            'is_trial': False,
            'premium_required': premium_required,
            'trial_available': False,
            'remaining_seconds': None,
            'days_left': None,
            'kofi_url': 'https://ko-fi.com/kava4',
        }

    if not premium_required:
        return {
            'allowed': True,
            'tier': 'Free',
            'display_name': 'AI enabled',
            'message': '',
            'license_valid': True,
            'is_trial': False,
            'is_dev': False,
            'premium_required': False,
            'dev_keys_enabled': dev_keys_enabled(),
            'trial_available': False,
            'remaining_seconds': None,
            'days_left': None,
            'kofi_url': 'https://ko-fi.com/kava4',
        }

    license_data = validate_license(key, activate_trial=False) if refresh else _refresh_if_stale(key)
    allowed = ai_access_allowed(license_data, key)
    trial = is_trial_license(key, license_data)

    message = ''
    if not license_data.get('valid'):
        if trial or license_data.get('trial_available'):
            message = 'AI is for Ko-fi supporters. Recoil remains free — add your supporter key in Global Settings.'
        else:
            message = 'Enter a valid supporter license key in Global Settings to unlock AI.'
    elif trial:
        message = 'Free trial does not include AI. Support on Ko-fi to unlock AimSync AI.'
    elif not allowed:
        message = 'AI requires an active supporter license.'

    if is_dev_license_key(key) and not dev_keys_enabled():
        message = (
            'Dev keys are disabled in this build. '
            'Use scripts\\run_dev.bat, set AIMSYNC_DEV=1, or AIMSYNC_ALLOW_DEV_KEYS=1.'
        )
        allowed = False

    return {
        'allowed': allowed,
        'tier': license_data.get('tier', 'Free'),
        'display_name': license_data.get('display_name'),
        'message': message,
        'license_valid': bool(license_data.get('valid')),
        'is_trial': trial,
        'is_dev': bool(license_data.get('dev')) or str(license_data.get('tier', '')).lower() == 'dev',
        'dev_keys_enabled': dev_keys_enabled(),
        'premium_required': True,
        'trial_available': bool(license_data.get('trial_available')),
        'remaining_seconds': license_data.get('remaining_seconds'),
        'days_left': license_data.get('days_left'),
        'kofi_url': 'https://ko-fi.com/kava4',
    }
