"""Weapon icon filenames (CS2 inventory-style SVG basenames)."""

from __future__ import annotations

# KryptAim weapon id -> icon file in web/static/weapons/
WEAPON_ICON_FILES: dict[str, str] = {
    'assault_rifle': 'ak47.svg',
    'm4a4': 'm4a1.svg',
    'm4a1s': 'm4a1_silencer.svg',
    'famas': 'famas.svg',
    'galil': 'galilar.svg',
    'mp9': 'mp9.svg',
    'mac10': 'mac10.svg',
    'mp7': 'mp7.svg',
    'mp5sd': 'mp5sd.svg',
    'p90': 'p90.svg',
    'ump45': 'ump45.svg',
    'bizon': 'bizon.svg',
}

DEFAULT_ICON_SOURCE = (
    r'e:\projects\cs2-webradar-usermode\release\dist\assets\icons'
)
