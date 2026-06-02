# Weapons and games

Game Engine loads weapon profiles from `Recoil/games/<game_id>.py` via `Recoil/weapon_data.py`.

## Active game selection

Set `active_game` in config or **Global Settings**. The dashboard lists all games in `SUPPORTED_GAMES` (`Server/app.py`); only some have `supported: true` and complete data files.

## Implemented game modules

| File | Game |
|------|------|
| `Recoil/games/cs2.py` | Counter-Strike 2 |
| `Recoil/games/valorant.py` | Valorant |
| `Recoil/games/pubg.py` | PUBG |
| `Recoil/games/r6s.py` | Rainbow Six Siege |
| `Recoil/games/rust.py` | Rust |

## Profile structure

Each game module exposes weapon attributes as lists of `[x, y, delay]` tuples (or equivalent structures consumed by `Recoil/recoil.py`).

Example attribute names (CS2):

- `assault_rifle`
- Additional rifles / SMGs as defined in the module

Use `WeaponData.get_game_data(active_game)` to enumerate weapon names in the UI.

## Adding a new game

1. Create `Recoil/games/newgame.py` with weapon lists.
2. Register the game in `SUPPORTED_GAMES` in `Server/app.py`.
3. Set `supported: true` when profiles are ready.
4. Test sensitivity scaling in Game Engine.

## Pattern Generator workflow

Use the standalone [Pattern Generator](../development/pattern-generator.md) to extract sprays from GIFs, then paste generated arrays into the appropriate game module.

## See also

- [Game Engine](../user-guide/game-engine.md)
