# Game Engine

Game Engine applies built-in per-weapon recoil profiles for supported titles. Profiles are scaled by your in-game sensitivity and executed like Recoil Lab patterns in the background loop.

**Access:** Donator license or active [free trial](licensing.md).

## Supported games (current)

| Game ID | Status |
|---------|--------|
| Counter-Strike 2 (`cs2`) | Supported |
| Valorant (`valorant`) | Supported |
| PUBG (`pubg`) | Supported |
| Rainbow Six Siege (`r6s`) | Supported |
| Rust (`rust`) | Supported |
| Apex, CoD, Warzone, others | Listed; profiles may be incomplete |

Switch **Active game** in Global Settings before opening Game Engine.

## Configuration

| Setting | Description |
|---------|-------------|
| Weapon | Profile name (e.g. assault rifle, SMG variants) |
| Sensitivity | Must match in-game sensitivity for correct scale |
| Loop | Repeat spray pattern while firing |

## Weapon cycle hotkey

Assign **Cycle weapon keybind** in Global Settings to rotate through weapons defined for the active game without opening the UI.

The hotkey thread polls at ~100 Hz and persists the new weapon to `config.json`.

## How scaling works

Weapon data lives under `Recoil/games/<game>.py` as coordinate lists. At runtime the engine:

1. Loads the profile for the selected weapon
2. Applies sensitivity multiplier from config
3. Applies safety randomization and global X/Y scale
4. Sends movements via hardware or software manager

## Related API

- `POST /api/recoil/game_weapon`
- `POST /api/recoil/game_sensitivity`
- `POST /api/recoil/game_loop`
- `POST /api/recoil/active_game`
- `GET /api/recoil/current_weapon`
- `POST /api/recoil/cs2_weapon` (legacy alias paths)

## See also

- [Weapons and games](../reference/weapons-and-games.md)
- [Architecture](../development/architecture.md)
