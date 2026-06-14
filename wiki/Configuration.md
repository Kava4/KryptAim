# Configuration

Settings persist in `config.json`.

---

## File location

```
%APPDATA%\KryptAim\config.json
```

Defaults defined in `app/core/config.py` (`DEFAULTS`).

---

## Recoil keys

| Key | Default | Description |
|-----|---------|-------------|
| `recoil_enabled` | `false` | Master switch |
| `recoil_keybind` | `M4` | Toggle hotkey |
| `recoil_mode` | `CS2` | Game mode |
| `mouse_input_method` | `makcu` | `makcu` or `win32` (dev) |
| `recoil_require_rmb` | `false` | Require right-click |
| `recoil_randomisation` | `false` | Jitter |
| `recoil_x_control` / `recoil_y_control` | `100` | Scale % |
| `recoil_cs2_settings` | object | Active weapon + sensitivity |

---

## AI keys

| Key | Default | Description |
|-----|---------|-------------|
| `ai_enabled` | `false` | Engine on/off |
| `ai_model_path` | `""` | Model file path |
| `ai_my_team` | `""` | `ct` / `t` for enemy filter |
| `ai_player_class` | `""` | Target body class |
| `ai_head_class` | `""` | Head class (optional) |
| `ai_capture_mode` | `ndi` | Capture backend |
| `ai_ndi_source` | `""` | NDI name |
| `ai_detection_conf` | `0.25` | Threshold |
| `ai_aim_enabled` | `false` | Aim assist |
| `ai_trigger_enabled` | `false` | Auto trigger |
| `ai_assist_mode` | `trigger` | `trigger` / `aim` / `both` |

---

## License keys (when premium AI enabled)

| Key | Description |
|-----|-------------|
| `license_key` | Supporter key from Ko-fi cloud |
| `is_premium` | Cached validation flag |

---

## Paths on disk

| Data | Path |
|------|------|
| Models | `%APPDATA%\KryptAim\models\` |
| AI runtime | `%APPDATA%\KryptAim\runtime\` |
| Updates | `%APPDATA%\KryptAim\updates\` |

---

## Related

- [AI Engine](AI-Engine)
- [Global settings](Global-Settings)
