# Game Engine

Per-game weapon profiles with sensitivity scaling.

---

## CS2

1. Select **active game**: CS2.
2. Pick **weapon** (AK-47, M4A1-S, etc.).
3. Set **in-game sensitivity** to match CS2 settings.
4. Enable recoil + hold hotkey in-game.

Patterns live in `Recoil/games/cs2.py` — scaled at runtime based on your sensitivity.

---

## Weapon cycling

Assign **weapon cycle hotkey** or per-weapon direct binds in Global settings.

Current weapon is polled from config and shown in the UI.

---

## Adding weapons

1. Use [Pattern Generator](Pattern-Generator) to build a spray from GIF/image.
2. **Append to Game Data** writes into `Recoil/games/<game>.py` with `.bak` backup.
3. Restart not required — reload from UI.

See [Weapons and games](Weapons-and-Games).
