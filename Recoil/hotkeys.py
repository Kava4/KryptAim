import ctypes
from dataclasses import dataclass
from typing import Iterable

from Makcu.makcu_manager import makcu_manager
from Makcu.software_manager import software_manager


MODIFIER_ORDER = ('ctrl', 'alt', 'shift')
MODIFIER_ALIASES = {
    'ctrl': 'ctrl',
    'control': 'ctrl',
    'alt': 'alt',
    'shift': 'shift',
}
SPECIAL_KEY_ALIASES = {
    'lmb': 'LMB',
    'rmb': 'RMB',
    'mmb': 'MMB',
    'none': 'None',
    'lmenu': 'alt',
    'rmenu': 'alt',
    'lalt': 'alt',
    'ralt': 'alt',
    'menu': 'alt',
    'mouse1': 'LMB',
    'mouse2': 'RMB',
    'mouse3': 'MMB',
    'middlemouse': 'MMB',
    'middle_mouse': 'MMB',
    'mb3': 'MMB',
    'm4': 'M4',
    'm5': 'M5',
    'mouse4': 'M4',
    'mouse5': 'M5',
}
MOUSE_KEYS = {'LMB', 'RMB', 'MMB', 'M4', 'M5'}
VK_CODES = {
    'tab': 0x09,
    'enter': 0x0D,
    'esc': 0x1B,
    'escape': 0x1B,
    'space': 0x20,
    'home': 0x24,
    'end': 0x23,
    'pageup': 0x21,
    'pagedown': 0x22,
    'insert': 0x2D,
    'delete': 0x2E,
    'up': 0x26,
    'down': 0x28,
    'left': 0x25,
    'right': 0x27,
    'ctrl': 0x11,
    'alt': 0x12,
    'lalt': 0xA4,
    'ralt': 0xA5,
    'shift': 0x10,
    'lshift': 0xA0,
    'rshift': 0xA1,
    'lctrl': 0xA2,
    'rctrl': 0xA3,
}

for index in range(1, 13):
    VK_CODES[f'f{index}'] = 0x6F + index

for index in range(10):
    VK_CODES[str(index)] = 0x30 + index

for code in range(ord('a'), ord('z') + 1):
    VK_CODES[chr(code)] = code


class HotkeyValidationError(ValueError):
    pass


@dataclass(frozen=True)
class HotkeySpec:
    raw: str
    normalized: str
    primary_key: str | None
    modifiers: tuple[str, ...]

    @property
    def is_disabled(self) -> bool:
        return self.primary_key is None


_hotkey_binding_active = False


def set_hotkey_binding_active(active: bool) -> None:
    global _hotkey_binding_active
    _hotkey_binding_active = active


def is_hotkey_binding_active() -> bool:
    return _hotkey_binding_active


class HotkeyStateTracker:
    def __init__(self) -> None:
        self._states: dict[str, bool] = {}

    def reset(self, action_id: str) -> None:
        self._states[action_id] = False

    def is_pressed_once(self, action_id: str, hotkey_value: str | None) -> bool:
        hotkey = parse_hotkey(hotkey_value)
        if hotkey.is_disabled:
            self._states[action_id] = False
            return False

        pressed = is_hotkey_pressed(hotkey)
        previous = self._states.get(action_id, False)
        self._states[action_id] = pressed
        return pressed and not previous


def normalize_hotkey_string(hotkey_value: str | None) -> str:
    return parse_hotkey(hotkey_value).normalized


def parse_hotkey(hotkey_value: str | None) -> HotkeySpec:
    raw_value = str(hotkey_value or '').strip()
    if not raw_value or raw_value.lower() == 'none':
        return HotkeySpec(raw=raw_value, normalized='None', primary_key=None, modifiers=())

    tokens = [token.strip().lower() for token in raw_value.split('+') if token.strip()]
    if not tokens:
        return HotkeySpec(raw=raw_value, normalized='None', primary_key=None, modifiers=())

    modifiers: list[str] = []
    primary_key: str | None = None

    for token in tokens:
        modifier = MODIFIER_ALIASES.get(token)
        if modifier:
            if modifier not in modifiers:
                modifiers.append(modifier)
            continue

        candidate = _normalize_primary_key(token)
        if primary_key is not None:
            raise HotkeyValidationError('Use only one primary key per hotkey.')
        primary_key = candidate

    if primary_key is None:
        if len(modifiers) == 1:
            primary_key = modifiers[0]
            modifiers = []
        else:
            raise HotkeyValidationError('Hotkey must include one primary key.')
    if len(modifiers) > 2:
        raise HotkeyValidationError('Use at most two modifiers per hotkey.')

    ordered_modifiers = tuple(modifier for modifier in MODIFIER_ORDER if modifier in modifiers)
    normalized_parts = [*ordered_modifiers, primary_key.lower() if primary_key not in MOUSE_KEYS else primary_key]
    normalized = '+'.join(normalized_parts)
    return HotkeySpec(raw=raw_value, normalized=normalized, primary_key=primary_key, modifiers=ordered_modifiers)


def validate_hotkey_bindings(
    global_toggle: str | None,
    cycle_hotkey: str | None,
    direct_binds: dict[str, str] | None,
    *,
    ai_aim_keybind: str | None = None,
    ai_second_aim_keybind: str | None = None,
    ai_engine_toggle_hotkey: str | None = None,
) -> None:
    claimed: dict[str, str] = {}
    _claim_binding(claimed, global_toggle, 'Global toggle')
    _claim_binding(claimed, cycle_hotkey, 'Weapon cycle')
    _claim_binding(claimed, ai_aim_keybind, 'AI aim hold (primary)')
    _claim_binding(claimed, ai_second_aim_keybind, 'AI aim hold (secondary)')
    _claim_binding(claimed, ai_engine_toggle_hotkey, 'AI engine toggle')

    for hotkey_value, weapon in (direct_binds or {}).items():
        if not weapon:
            continue
        _claim_binding(claimed, hotkey_value, f'Weapon bind for {weapon}')


def is_hotkey_pressed(hotkey: HotkeySpec | str | None) -> bool:
    spec = hotkey if isinstance(hotkey, HotkeySpec) else parse_hotkey(hotkey)
    if spec.is_disabled or not spec.primary_key:
        return False

    if not all(_is_key_pressed(modifier) for modifier in spec.modifiers):
        return False
    return _is_key_pressed(spec.primary_key)


def get_bound_weapon(config: dict, tracker: HotkeyStateTracker) -> str | None:
    for hotkey_value, weapon in (config.get('weapon_direct_binds') or {}).items():
        if weapon and tracker.is_pressed_once(f'weapon:{weapon}:{hotkey_value}', hotkey_value):
            return weapon
    return None


def _claim_binding(claimed: dict[str, str], hotkey_value: str | None, label: str) -> None:
    spec = parse_hotkey(hotkey_value)
    if spec.is_disabled:
        return
    owner = claimed.get(spec.normalized)
    if owner:
        raise HotkeyValidationError(f'Hotkey "{spec.normalized}" conflicts with {owner.lower()}.')
    claimed[spec.normalized] = label


def _normalize_primary_key(token: str) -> str:
    alias = SPECIAL_KEY_ALIASES.get(token)
    if alias:
        return alias

    if token in VK_CODES:
        return token

    raise HotkeyValidationError(f'Unsupported key "{token}".')


def _is_key_pressed(key_name: str) -> bool:
    if key_name in MOUSE_KEYS:
        return makcu_manager.get_button_state(key_name)

    vk_code = VK_CODES.get(key_name.lower())
    if vk_code is None:
        return False
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000)
