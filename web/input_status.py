"""Shared Makcu / input method status for web UI."""

from __future__ import annotations

from app.core.config import load_config
from app.makcu.manager import makcu_manager


def refresh_makcu_connection() -> None:
    """Try to connect once; never treat dev fallback as hardware."""
    if makcu_manager.is_hardware():
        return
    if not makcu_manager.dev_mode:
        makcu_manager.connect()


def get_input_status() -> dict:
    config = load_config()
    method = (config.get('mouse_input_method') or 'makcu').strip().lower()

    if method == 'win32':
        return {
            'input_label': 'Win32',
            'input_status': 'Local mouse (dev)',
            'input_style': 'bg-amber-500/10 border-amber-500/50 text-amber-300',
            'input_dot': 'bg-amber-500',
            'is_unsafe': True,
            'integrity_level': 'Low (Unsafe)',
            'integrity_color': 'bg-red-500/10 border-red-500/50 text-red-400',
            'dot_color': 'bg-red-500',
            'makcu_hardware': False,
            'makcu_dev_fallback': False,
        }

    refresh_makcu_connection()
    hardware = makcu_manager.is_hardware()
    dev_fallback = makcu_manager.dev_mode and not hardware

    if hardware:
        input_status = 'Connected'
        input_style = 'bg-green-500/10 border-green-500/50 text-green-400 shadow-[0_0_10px_rgba(34,197,94,0.1)]'
        input_dot = 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse'
        is_unsafe = False
    elif dev_fallback:
        input_status = 'Dev fallback'
        input_style = 'bg-amber-500/10 border-amber-500/50 text-amber-300'
        input_dot = 'bg-amber-500'
        is_unsafe = True
    else:
        input_status = makcu_manager.last_error or 'Disconnected'
        input_style = 'bg-red-500/10 border-red-500/50 text-red-400'
        input_dot = 'bg-red-500'
        is_unsafe = True

    integrity_level = 'High (Safe)' if not is_unsafe else 'Low (Unsafe)'
    integrity_color = (
        'bg-blue-500/10 border-blue-500/50 text-blue-400'
        if not is_unsafe
        else 'bg-red-500/10 border-red-500/50 text-red-400'
    )
    dot_color = 'bg-blue-500' if not is_unsafe else 'bg-red-500'

    return {
        'input_label': 'Makcu',
        'input_status': input_status,
        'input_style': input_style,
        'input_dot': input_dot,
        'is_unsafe': is_unsafe,
        'integrity_level': integrity_level,
        'integrity_color': integrity_color,
        'dot_color': dot_color,
        'makcu_hardware': hardware,
        'makcu_dev_fallback': dev_fallback,
    }
