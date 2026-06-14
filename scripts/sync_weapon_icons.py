"""Copy CS2 weapon SVG icons into web/static/weapons/."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from app.recoil.weapon_icons import DEFAULT_ICON_SOURCE, WEAPON_ICON_FILES


def _normalize_svg_fill(content: str) -> str:
    """Ensure silhouettes render white on dark UI (ak47.svg omits fill in source)."""
    if 'fill="#FFFFFF"' in content or "fill='#FFFFFF'" in content:
        return content
    marker = 'clip-rule="evenodd"'
    if marker in content:
        return content.replace(marker, f'{marker} fill="#FFFFFF"', 1)
    return content


def main() -> int:
    src_root = Path(os.environ.get('KRYPTAIM_WEAPON_ICONS', DEFAULT_ICON_SOURCE))
    if not src_root.is_dir():
        print(f'ERROR: icon source not found: {src_root}')
        print('Set KRYPTAIM_WEAPON_ICONS to your cs2-webradar icons folder.')
        return 1

    out = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'weapons'
    out.mkdir(parents=True, exist_ok=True)

    copied = 0
    for weapon_id, icon_name in WEAPON_ICON_FILES.items():
        src = src_root / icon_name
        if not src.is_file():
            print(f'WARN missing source icon: {src}')
            continue
        dest = out / f'{weapon_id}.svg'
        svg = src.read_text(encoding='utf-8')
        dest.write_text(_normalize_svg_fill(svg), encoding='utf-8')
        copied += 1
        print(f'OK  {icon_name} -> {dest.name}')

    print(f'\nCopied {copied}/{len(WEAPON_ICON_FILES)} icons to {out}')
    return 0 if copied else 1


if __name__ == '__main__':
    raise SystemExit(main())
