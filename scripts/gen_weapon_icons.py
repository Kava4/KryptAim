"""Generate stylized weapon SVG icons for the web UI."""

from __future__ import annotations

from pathlib import Path

WEAPONS: dict[str, tuple[str, str, str]] = {
    'assault_rifle': ('AK-47', '#c45c26', 'rifle'),
    'm4a4': ('M4A4', '#4ade80', 'rifle'),
    'm4a1s': ('M4A1-S', '#22d3ee', 'rifle'),
    'famas': ('FAMAS', '#a3e635', 'rifle'),
    'galil': ('GALIL', '#fbbf24', 'rifle'),
    'mp9': ('MP9', '#94a3b8', 'smg'),
    'mac10': ('MAC-10', '#f472b6', 'smg'),
    'mp7': ('MP7', '#818cf8', 'smg'),
    'mp5sd': ('MP5-SD', '#2dd4bf', 'smg'),
    'p90': ('P90', '#fb923c', 'smg'),
    'ump45': ('UMP-45', '#e879f9', 'smg'),
    'bizon': ('BIZON', '#fcd34d', 'smg'),
}

RIFLE_PATH = 'M8 30h34l4 6h8l-3-6h10v-6H52l-6-4H24l-4 4H8v6z'
SMG_PATH = 'M10 28h22l3 5h6l-2-5h8v-5H38l-4-3H18l-3 3h-5v5z'


def main() -> None:
    out = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'weapons'
    out.mkdir(parents=True, exist_ok=True)
    for weapon_id, (label, color, kind) in WEAPONS.items():
        path = RIFLE_PATH if kind == 'rifle' else SMG_PATH
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 88 56" role="img" aria-label="{label}">
  <rect width="88" height="56" rx="10" fill="#171717" stroke="#ffffff14" stroke-width="1"/>
  <path d="{path}" fill="{color}" opacity="0.92"/>
  <text x="44" y="50" text-anchor="middle" fill="#ffffffb3" font-family="Inter,Arial,sans-serif" font-size="9" font-weight="600">{label}</text>
</svg>'''
        (out / f'{weapon_id}.svg').write_text(svg, encoding='utf-8')
    print(f'Wrote {len(WEAPONS)} icons to {out}')


if __name__ == '__main__':
    main()
