"""Environment helpers — KryptAim vars with legacy KryptAim aliases."""

from __future__ import annotations

import os

_ON = frozenset({'1', 'true', 'yes', 'on'})


def env_flag(name: str) -> bool:
    for prefix in ('KRYPTAIM', 'AIMSYNC'):
        if os.environ.get(f'{prefix}_{name}', '').strip().lower() in _ON:
            return True
    return False


def env_get(name: str, default: str = '') -> str:
    for prefix in ('KRYPTAIM', 'AIMSYNC'):
        value = os.environ.get(f'{prefix}_{name}', '').strip()
        if value:
            return value
    return default
