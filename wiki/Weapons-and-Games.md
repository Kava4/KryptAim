# Weapons and games

---

## Supported games

| Game id | Module | Notes |
|---------|--------|-------|
| `cs2` | `Recoil/games/cs2.py` | Primary supported title |

`active_game` in config selects the engine.

---

## CS2 weapons

Weapon profiles are Python lists in `cs2.py` — each weapon has:
- Named pattern steps `(dx, dy, delay_seconds)`
- Metadata for UI weapon picker

Sensitivity scaling: `recoil_game_settings.sensitivity` scales pattern magnitude to match in-game sens.

---

## Adding / editing weapons

1. **Pattern Generator** → generate from spray capture → **Append to Game Data**.
2. Manual edit `Recoil/games/cs2.py` (backup created automatically on append).
3. Reload weapon in Game Engine tab.

Canonical format matches `weapon_data.py` style (1:1 export mode).

---

## Weapon hotkeys

- **Weapon cycle hotkey** — cycle through list.
- **Weapon direct binds** — map keys to specific weapons (`weapon_direct_binds` in config).
