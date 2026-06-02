# Quick start

This guide gets you from a fresh install to an active profile in about five minutes.

## 1. Install and launch AimSync

Use the latest build from [GitHub Releases](https://github.com/Kava4/AimSync/releases/latest). The public source repository does **not** include all files needed to run the app from a clone—see [Installation](installation.md).

After installing, start AimSync from the release package. The dashboard opens on **Global Settings** by default.

## 2. Connect input method

| Method | When to use |
|--------|-------------|
| **Hardware** | Makcu connected; lowest-level mouse injection |
| **Software** | Testing without hardware; uses Windows SendInput |

Set this under **Global Settings → Input method**.

## 3. Confirm access mode

For now, AimSync runs in **free access mode**: Game Engine and cloud upload are unlocked for everyone.

In **Global Settings**, you should see **FREE ACCESS ENABLED** in the access status row.

## 4. Enable the master switch

Toggle **Master Switch** on or assign a hotkey (M4/M5 recommended). Recoil compensation only runs when the master switch is active and your fire conditions are met.

## 5. Choose a recoil mode

| Tab | Use case |
|-----|----------|
| **Simple Recoil** | Fixed X/Y pull per shot |
| **Recoil Lab** | Custom multi-step patterns with the visualizer |
| **Game Engine** | Built-in weapon sprays (CS2, Valorant, PUBG, R6S, Rust, …) |

Optional: in **Recoil Lab**, use **Pattern Generator** to import a spray image/GIF and convert it into recoil steps.

For Game Engine:

1. Open the **Game Engine** tab.
2. Select your game and weapon.
3. Match **in-game sensitivity** to the value in AimSync.

## 6. Test safely

- Use an offline or private environment first.
- Start with low Y scale and no randomization.
- Confirm movement direction before competitive play.

## Related pages

- [Global settings](../user-guide/global-settings.md)
- [Game Engine](../user-guide/game-engine.md)
- [Configuration reference](../reference/configuration.md)
