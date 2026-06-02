import re
from difflib import SequenceMatcher

from Recoil.weapon_data import WeaponData


ALIASES = {
    'ak': 'ak47',
    'ak47': 'ak47',
    'ak-47': 'ak47',
    'm4a1s': 'm4a1s',
    'm4a1-s': 'm4a1s',
    'm4a4': 'm4a4',
    'aug': 'aug',
    'awp': 'awp',
    'famas': 'famas',
    'galil': 'galilar',
    'galilar': 'galilar',
    'g3sg1': 'g3sg1',
    'scar20': 'scar20',
    'mac10': 'mac10',
    'mp5': 'mp5sd',
    'mp5sd': 'mp5sd',
    'mp7': 'mp7',
    'mp9': 'mp9',
    'p90': 'p90',
    'bizon': 'ppbizon',
    'ppbizon': 'ppbizon',
    'ump45': 'ump45',
    'xm1014': 'xm1014',
    'mag7': 'mag7',
    'nova': 'nova',
    'sawedoff': 'sawedoff',
    'sawed-off': 'sawedoff',
    'negev': 'negev',
    'm249': 'm249',
    'deagle': 'deagle',
    'deserteagle': 'deagle',
    'elite': 'elite',
    'dualberettas': 'elite',
    'fiveseven': 'fiveseven',
    'five-seven': 'fiveseven',
    'glock': 'glock',
    'glock18': 'glock',
    'p2000': 'p2000',
    'p250': 'p250',
    'tec9': 'tec9',
    'tec-9': 'tec9',
    'usps': 'usp',
    'usp-s': 'usp',
    'usp': 'usp',
    'cz75': 'cz75a',
    'cz75a': 'cz75a',
    'revolver': 'revolver',
}


def get_cs2_weapon_ids() -> list[str]:
    game_data = WeaponData.get_game_data('cs2')
    weapons = [
        attr for attr in dir(game_data)
        if not attr.startswith('_') and isinstance(getattr(game_data, attr), list)
    ]
    weapons.sort()
    return weapons


def normalize_weapon_name(raw_text: str) -> str:
    return _normalize_text(raw_text)


def match_weapon_text(raw_text: str, minimum_score: float = 0.55) -> tuple[str | None, float]:
    cleaned = _normalize_text(raw_text)
    if not cleaned:
        return None, 0.0

    alias_match = ALIASES.get(cleaned)
    if alias_match:
        return alias_match, 1.0

    best_weapon = None
    best_score = 0.0
    for weapon_id in get_cs2_weapon_ids():
        candidates = {weapon_id, weapon_id.replace('_', ''), weapon_id.replace('_', ' ')}
        for alias, target in ALIASES.items():
            if target == weapon_id:
                candidates.add(alias)

        score = max(SequenceMatcher(None, cleaned, candidate).ratio() for candidate in candidates)
        if score > best_score:
            best_weapon = weapon_id
            best_score = score

    if best_score < minimum_score:
        return None, best_score
    return best_weapon, best_score


def _normalize_text(raw_text: str) -> str:
    cleaned = (raw_text or '').strip().lower()
    cleaned = cleaned.replace('|', 'l')
    cleaned = re.sub(r'[^a-z0-9]+', '', cleaned)
    return cleaned
