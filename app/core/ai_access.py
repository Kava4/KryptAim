"""AI access rules: cloud supporter keys + free-tier daily Vision AI quota."""

from __future__ import annotations

import os

from app.core.ai_free_quota import (
    get_ai_free_quota_manager,
    quota_feature_enabled,
    unlimited_quota_status,
)
from app.core.config import load_config
from app.core.feature_flags import ai_premium_required
from app.core.license_cloud import (
    invalidate_license_cache,
    is_dev_key,
    supporter_plan_status,
    supporter_unlock_active,
    validate_license,
)


def donor_unlock_active(*, refresh: bool = False) -> bool:
    if os.environ.get('KRYPTAIM_AI_UNLOCK', '').strip().lower() in {'1', 'true', 'yes', 'on'}:
        return True
    key = (load_config().get('license_key') or '').strip()
    if not key:
        return False
    return supporter_unlock_active(key, refresh=refresh)


def _base_access_status(*, refresh: bool = False) -> dict:
    premium = ai_premium_required(refresh=refresh)
    key = (load_config().get('license_key') or '').strip()
    license_result = validate_license(key, refresh=refresh) if key else {
        'valid': False,
        'tier': 'Free',
        'display_name': '',
        'message': '',
    }
    valid = bool(license_result.get('valid'))
    tier = str(license_result.get('tier') or 'Free')
    dev = is_dev_key(key) and valid

    if premium:
        allowed = valid and not license_result.get('dev_disabled')
        message = ''
        if not key:
            message = 'Enter your supporter key to unlock Vision AI.'
        elif not allowed:
            message = license_result.get('message') or 'Invalid or revoked supporter key.'
        return {
            'allowed': allowed,
            'premium_required': True,
            'donor_unlock': allowed,
            'license_valid': valid,
            'is_trial': False,
            'tier': tier,
            'display_name': license_result.get('display_name') or '',
            'message': message,
            'dev': dev,
        }

    return {
        'allowed': True,
        'premium_required': False,
        'donor_unlock': donor_unlock_active(refresh=refresh),
        'license_valid': valid,
        'is_trial': False,
        'tier': tier if valid else 'Free',
        'display_name': license_result.get('display_name') or '',
        'message': license_result.get('message') or '',
        'dev': dev,
    }


def resolve_ai_access(*, refresh: bool = False) -> dict:
    status = _base_access_status(refresh=refresh)
    premium = bool(status.get('premium_required'))

    if premium:
        key = (load_config().get('license_key') or '').strip()
        valid = bool(status.get('license_valid'))
        allowed = bool(status.get('allowed'))
        plan_info = supporter_plan_status(key, refresh=refresh) if key and valid else {}
        unlimited = bool(plan_info.get('unlimited')) if valid else False
        days_left = plan_info.get('days_left') if valid else None
        status['free_quota'] = unlimited_quota_status(
            donor=allowed,
            plan='unlimited' if unlimited else ('monthly' if allowed else 'free'),
            days_left=days_left if allowed and not unlimited else None,
        )
        if allowed and not unlimited and days_left is not None:
            status['days_left'] = days_left
            status['supporter_plan'] = 'monthly'
        elif allowed and unlimited:
            status['supporter_plan'] = 'unlimited'
        return status

    if status.get('donor_unlock'):
        key = (load_config().get('license_key') or '').strip()
        plan_info = supporter_plan_status(key, refresh=refresh) if key else {}
        plan = str(plan_info.get('plan') or 'monthly')
        unlimited = bool(plan_info.get('unlimited'))
        days_left = plan_info.get('days_left')
        status['allowed'] = True
        status['donor_unlock'] = True
        status['supporter_plan'] = plan
        status['days_left'] = days_left
        status['free_quota'] = unlimited_quota_status(
            donor=True,
            plan='unlimited' if unlimited else 'monthly',
            days_left=days_left if not unlimited else None,
        )
        if unlimited:
            status.setdefault('message', '')
        else:
            left = days_left if days_left is not None else '?'
            status.setdefault('message', '')
            status['supporter_hint'] = f'Monthly supporter · {left} days left'
        return status

    if not quota_feature_enabled(premium_required=False):
        status['allowed'] = True
        status['free_quota'] = unlimited_quota_status(donor=False)
        return status

    quota = get_ai_free_quota_manager().public_status()
    status['free_quota'] = quota
    status['donor_unlock'] = False
    status['allowed'] = not quota['exhausted']
    if quota['exhausted']:
        limit = quota.get('limit_minutes', 120)
        status['message'] = (
            f'Free Vision AI limit reached ({limit} min/day). '
            'Activate with your supporter key for monthly or unlimited access.'
        )
    else:
        mins = quota.get('remaining_minutes', 0)
        status.setdefault('message', '')
        status['free_quota_hint'] = f'{mins} min free today'
    return status


def can_enable_ai_engine(*, refresh: bool = False) -> tuple[bool, dict]:
    status = resolve_ai_access(refresh=refresh)
    return bool(status.get('allowed')), status


def invalidate_ai_access_cache() -> None:
    invalidate_license_cache()
