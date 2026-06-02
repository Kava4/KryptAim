# Configuration reference

## File locations

| Build | Path |
|-------|------|
| Development | `<project-root>/config.json` (or `Config/config.json` if present) |
| Frozen `.exe` | `%APPDATA%\AimSync\config.json` |

Saved patterns: `<base>/saved_patterns/*.json`

## Top-level keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `recoil_enabled` | bool | `false` | Master switch |
| `recoil_keybind` | string | `"M4"` | Master toggle button |
| `recoil_mode` | string | `"simple"` | Last mode tab: `simple`, `advanced`, `CS2` |
| `recoil_require_rmb` | bool | `false` | Require aim (RMB) while compensating |
| `recoil_randomisation` | bool | `false` | Enable jitter |
| `recoil_random_strength` | float | `5.0` | Randomization intensity |
| `recoil_cycle_keybind` | string | `"None"` | Game Engine weapon cycle |
| `recoil_x_control` | number | `100` | Global X scale % |
| `recoil_y_control` | number | `100` | Global Y scale % |
| `recoil_safety_features_enabled` | bool | `true` | Master safety toggle |
| `shutdown_on_app_stop` | bool | `false` | Shutdown OS on quit |
| `active_game` | string | `"cs2"` | Game Engine game id |
| `license_key` | string | `""` | Donator key (empty for trial-only) |
| `is_premium` | bool | `false` | Mirror of last license check (not authoritative) |
| `recoil_input_method` | string | `"hardware"` | `hardware` or `software` |
| `cloud_username` | string | optional | Author name for cloud uploads |

## Nested objects

### `recoil_simple_settings`

| Key | Default | Description |
|-----|---------|-------------|
| `recoil_x` | `0` | Horizontal pull |
| `recoil_y` | `0` | Vertical pull |
| `recoil_delay` | `50` | ms between steps |

### `recoil_advanced_settings`

| Key | Description |
|-----|-------------|
| `recoil_loop` | Repeat pattern |
| `recoil_selected_pattern` | Active step array |
| `recoil_active_pattern_name` | Loaded save file name |

### `recoil_game_settings`

| Key | Default | Description |
|-----|---------|-------------|
| `weapon` | `"assault_rifle"` | Active weapon profile id |
| `sensitivity` | `1.0` | In-game sens multiplier |
| `recoil_loop` | `false` | Loop spray pattern |

## Example fragment

```json
{
  "recoil_enabled": true,
  "recoil_mode": "CS2",
  "active_game": "cs2",
  "recoil_game_settings": {
    "weapon": "assault_rifle",
    "sensitivity": 1.25,
    "recoil_loop": true
  }
}
```

## API access

Configuration is read/written by `Config/config_manager.py`. Most UI controls POST individual fields to Flask routes rather than replacing the whole file.
