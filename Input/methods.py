"""Resolve active mouse input method without touching Makcu."""

from __future__ import annotations

ALT_MOUSE_METHODS = frozenset({
    'win32',
    'ghub',
    'arduino',
    'rp2350',
    'teensy41',
    'kmbox_net',
    'kmbox_a',
    'razer',
})

_LEGACY_HARDWARE = frozenset({'hardware', 'makcu'})
_LEGACY_SOFTWARE = frozenset({'software', 'win32'})


def resolve_mouse_input_method(config: dict | None) -> str:
    """Return 'makcu' or an alt method key."""
    cfg = config or {}
    explicit = (cfg.get('mouse_input_method') or '').strip().lower()
    if explicit:
        if explicit in _LEGACY_HARDWARE:
            return 'makcu'
        if explicit in _LEGACY_SOFTWARE:
            return 'win32'
        if explicit in ALT_MOUSE_METHODS:
            return explicit
        return 'makcu'

    legacy = (cfg.get('recoil_input_method') or 'hardware').strip().lower()
    if legacy in _LEGACY_SOFTWARE:
        return 'win32'
    return 'makcu'


def use_alt_input(config: dict | None) -> bool:
    return resolve_mouse_input_method(config) != 'makcu'


def method_display_name(method: str) -> str:
    labels = {
        'makcu': 'Makcu',
        'win32': 'Win32 (SendInput)',
        'ghub': 'Logitech G Hub',
        'arduino': 'Arduino',
        'rp2350': 'RP2350',
        'teensy41': 'Teensy 4.1',
        'kmbox_net': 'KMBOX Net',
        'kmbox_a': 'KMBOX A',
        'razer': 'Razer (rzctl)',
    }
    return labels.get(method, method.upper())


def sync_legacy_recoil_input_method(config: dict) -> None:
    """Keep recoil_input_method in sync for older code paths."""
    method = resolve_mouse_input_method(config)
    if method == 'makcu':
        config['recoil_input_method'] = 'hardware'
    elif method == 'win32':
        config['recoil_input_method'] = 'software'
    else:
        config['recoil_input_method'] = 'hardware'
