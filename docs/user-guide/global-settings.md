# Global settings

The Global Settings tab controls system-wide behavior: power state, hotkeys, input method, licensing, and shutdown options.

## Master switch

| Control | Effect |
|---------|--------|
| Master toggle (UI) | Enables or disables the recoil engine |
| Keybind (e.g. M4, M5) | Toggles master state while the app runs |

When the master switch is off, no compensation is applied regardless of mode.

## Hotkeys

| Setting | Default | Description |
|---------|---------|-------------|
| Master keybind | `M4` | Toggle recoil on/off |
| Cycle weapon keybind | `None` | Cycle Game Engine weapons (when configured) |

Supported mouse buttons include LMB, RMB, MMB, M4, and M5.

## Require right mouse button

When enabled, recoil only runs while RMB (aim) is held. Recommended for ADS-only weapons.

## Input method

| Value | Description |
|-------|-------------|
| **hardware** | Movements via Makcu HID (recommended) |
| **software** | Movements via Windows SendInput |

Software mode shows a security notice in the UI. Use hardware for competitive scenarios where detection risk matters.

## Active game

Selects which game's weapon data Game Engine uses (`cs2`, `valorant`, `pubg`, `r6s`, `rust`, etc.). Only games marked supported in the UI have full profiles.

## Donator license

| Action | Description |
|--------|-------------|
| Enter key + **Apply** | Validates email or license key with Cloud API |
| **Start Free Trial** | Activates 2 hours/day trial bound to this PC |

Status shows a live countdown during an active trial. See [Licensing and free trial](licensing.md).

## Shutdown on app stop

When enabled, stopping AimSync from the UI also initiates a Windows shutdown (use with caution).

## Feedback

Use the feedback button in the sidebar to send bug reports to Discord via the Cloud API (includes HWID for support).

## Related API

- `POST /api/recoil/toggle`
- `POST /api/recoil/keybind`
- `POST /api/recoil/input_method`
- `POST /api/recoil/active_game`
- `GET /api/recoil/license_status`
- `POST /api/recoil/validate_license`

See [Local API](../reference/local-api.md).
