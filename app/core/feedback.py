"""Hardware id + user feedback relay to Cloud API (Discord webhook)."""

from __future__ import annotations

import uuid
from typing import Any

from app.core.cloud import submit_feedback as _cloud_submit_feedback

FEEDBACK_TYPES = frozenset({
    'UI / UX',
    'Recoil Engine',
    'Hardware',
    'AI Engine',
    'Bug Report',
    'General Bug',
    'Feature Request',
    'GiftMeCrypto',
    'Paysafe',
})


def get_hwid() -> str:
    return str(uuid.getnode())


def send_user_feedback(
    *,
    message: str,
    contact: str = '',
    feedback_type: str = 'Bug Report',
    hwid: str | None = None,
) -> dict[str, Any]:
    text = (message or '').strip()
    if not text:
        return {'success': False, 'message': 'Message cannot be empty.'}

    category = (feedback_type or 'Bug Report').strip()
    if category not in FEEDBACK_TYPES:
        category = 'Bug Report'

    payload = {
        'message': text,
        'contact': (contact or '').strip(),
        'type': category,
        'hwid': (hwid or get_hwid()).strip() or 'Unknown',
    }
    data, error = _cloud_submit_feedback(payload)
    if error:
        return {'success': False, 'message': error}
    if data and data.get('success') is False:
        return {
            'success': False,
            'message': str(data.get('message') or data.get('error') or 'Feedback rejected'),
        }
    return {'success': True, 'message': 'Sent successfully.'}


def send_support_code(
    *,
    provider: str,
    code: str,
    contact: str = '',
    hwid: str | None = None,
) -> dict[str, Any]:
    provider_key = (provider or '').strip().lower()
    mapping = {
        'giftmecrypto': 'GiftMeCrypto',
        'gift-me-crypto': 'GiftMeCrypto',
        'paysafe': 'Paysafe',
    }
    label = mapping.get(provider_key)
    if not label:
        return {'success': False, 'message': 'Unknown support provider.'}

    clean_code = (code or '').strip()
    if not clean_code:
        return {'success': False, 'message': 'Enter your code first.'}

    return send_user_feedback(
        message=f'{label} code: {clean_code}',
        contact=contact,
        feedback_type=label,
        hwid=hwid,
    )
