"""One-click AI setup presets (legacy quickstart parity)."""

from __future__ import annotations

from app.ai.ndi_control import get_ndi_sources, request_ndi_refresh


def apply_quickstart(*, trigger_only: bool = False, aim_only: bool = False) -> dict:
    """Return config updates for Quick setup / Aim setup / Trigger setup."""
    updates: dict = {
        'ai_enabled': True,
        'recoil_enabled': False,
        'ai_trigger_spray_block': True,
        'ai_aim_point': 'head',
        'ai_player_class': '',
        'ai_head_class': '',
    }
    if trigger_only:
        updates.update({
            'ai_assist_mode': 'trigger',
            'ai_trigger_always_on': True,
            'ai_trigger_keybind': 'M4',
            'ai_trigger_prediction_ms': 35,
            'ai_trigger_radius_px': 8,
            'ai_trigger_delay_ms': 30,
            'ai_trigger_cooldown_ms': 120,
        })
    elif aim_only:
        updates.update({
            'ai_assist_mode': 'aim',
            'ai_aim_always_on': True,
            'ai_aim_keybind': 'M4',
            'ai_aim_speed': 1.0,
            'ai_aim_max_px': 280,
            'ai_trigger_enabled': False,
            'ai_trigger_always_on': False,
        })
    else:
        updates.update({
            'ai_assist_mode': 'both',
            'ai_trigger_always_on': True,
            'ai_trigger_keybind': 'M4',
            'ai_trigger_prediction_ms': 35,
        })

    request_ndi_refresh()
    sources = get_ndi_sources()
    if sources and not updates.get('ai_ndi_source'):
        updates['ai_ndi_source'] = sources[0]
    return updates
