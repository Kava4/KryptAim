#!/usr/bin/env python3
"""Bake one aie1123-style weapon into weapon_data.py (dev, run once per weapon)."""

from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

AIE_URL = (
    'https://raw.githubusercontent.com/aie1123/CS2-No-Recoil-LOGITECH-Script-Macro/'
    'main/CS2-(2.40-2.60)Sens-no-rebound.lua'
)
AIE_CALIB_SENS = 2.53
PATTERN_BASELINE = 1.25
_TO_BASELINE = AIE_CALIB_SENS / PATTERN_BASELINE

_ROOT = Path(__file__).resolve().parents[1]
_WEAPON_DATA = _ROOT / 'app' / 'recoil' / 'weapon_data.py'

_WEAPON_META = {
    'galil': 'Galil AR',
    'mp7': 'MP7',
    'mp5sd': 'MP5-SD',
    'p90': 'P90',
    'ump45': 'UMP-45',
    'bizon': 'PP-Bizon',
}

AIE_SMG_BATCH = ('mp7', 'mp5sd', 'p90', 'ump45', 'bizon')


def _fetch_lua() -> str:
    return urllib.request.urlopen(AIE_URL, timeout=30).read().decode('utf-8', 'replace')


def _parse_weapon(lua: str, weapon_id: str) -> list[tuple[float, float, float]]:
    parts = re.split(r'\n(?=[a-z0-9]+\s*=\s*\{\{)', lua, flags=re.I)
    for part in parts:
        match = re.match(r'([a-z0-9]+)\s*=', part, re.I)
        if not match or match.group(1).lower() != weapon_id:
            continue
        steps: list[tuple[float, float, float]] = []
        for x_raw, y_raw, d_raw in re.findall(
            r'\{x\s*=\s*(-?\d+)\s*,\s*y\s*=\s*(-?\d+)\s*,\s*d\s*=\s*(\d+)\s*\}',
            part,
            re.I,
        ):
            x = round(int(x_raw) * _TO_BASELINE, 3)
            y = round(int(y_raw) * _TO_BASELINE, 3)
            delay = int(d_raw) / 1000.0
            steps.append((x, y, round(delay, 4)))
        return steps
    return []


def _format_block(weapon_id: str, pattern: list[tuple[float, float, float]]) -> str:
    lines = [f'        self.{weapon_id} = [']
    for x, y, delay in pattern:
        lines.append(f'            ({x}, {y}, {delay}),')
    lines.append('        ]')
    return '\n'.join(lines)


def _patch_weapon_data(weapon_id: str, pattern: list[tuple[float, float, float]], label: str) -> None:
    text = _WEAPON_DATA.read_text(encoding='utf-8')
    block = _format_block(weapon_id, pattern)

    block_re = re.compile(rf'        self\.{re.escape(weapon_id)} = \[.*?\n        \]\n', re.S)
    if block_re.search(text):
        text = block_re.sub(block + '\n\n', text)
    else:
        text = text.replace(
            '\n    @classmethod\n    def weapon_labels',
            '\n' + block + '\n\n    @classmethod\n    def weapon_labels',
        )

    profiles_match = re.search(r'(WEAPON_PROFILES: dict\[str, str\] = \{)(.*?)(\n    \})', text, re.S)
    if profiles_match:
        body = profiles_match.group(2)
        entry = f"\n        '{weapon_id}': 'timed',"
        if f"'{weapon_id}'" not in body:
            body = body.rstrip() + entry
        text = text[: profiles_match.start(2)] + body + text[profiles_match.end(2) :]

    labels_match = re.search(
        r"(def weapon_labels\(cls\) -> dict\[str, str\]:\n        return \{)(.*?)(\n        \})",
        text,
        re.S,
    )
    if labels_match:
        body = labels_match.group(2)
        entry = f"\n            '{weapon_id}': '{label}',"
        if f"'{weapon_id}'" not in body:
            body = body.rstrip() + entry
        text = text[: labels_match.start(2)] + body + text[labels_match.end(2) :]

    if "# smooth = " in text and 'timed' not in text.split('WEAPON_PROFILES')[0]:
        text = text.replace(
            '# smooth = 100ms eased move · spray = 30ms sleep + instant move',
            '# smooth · spray (fixed delay) · timed (per-step delay ms)',
        )

    _WEAPON_DATA.write_text(text, encoding='utf-8')


def _bake_one(lua: str, weapon_id: str) -> int:
    label = _WEAPON_META.get(weapon_id, weapon_id.upper())
    pattern = _parse_weapon(lua, weapon_id)
    if not pattern:
        print(f'No pattern for {weapon_id}', file=sys.stderr)
        return 1
    _patch_weapon_data(weapon_id, pattern, label)
    print(f'Baked {weapon_id}: {len(pattern)} steps @ calib {AIE_CALIB_SENS} -> baseline {PATTERN_BASELINE}')
    return 0


def main() -> int:
    arg = (sys.argv[1] if len(sys.argv) > 1 else 'galil').lower()
    weapon_ids = list(AIE_SMG_BATCH) if arg in ('all-smgs', 'smgs') else [arg]
    lua = _fetch_lua()
    failed = 0
    for weapon_id in weapon_ids:
        if _bake_one(lua, weapon_id) != 0:
            failed += 1
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
