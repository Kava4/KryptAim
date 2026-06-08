# Configuration

All settings persist in `config.json`.

---

## File locations

| Mode | Path |
|------|------|
| Dev (source) | `<project>/.aimsync-data/config.json` |
| Production | `%APPDATA%\AimSync\config.json` |
| Legacy | `%APPDATA%\AimSyncBeta\config.json` |

---

## Recoil keys (selection)

| Key | Default | Description |
|-----|---------|-------------|
| `recoil_enabled` | `false` | Master switch |
| `recoil_keybind` | `M4` | Toggle hotkey |
| `recoil_mode` | `simple` | `simple` / `advanced` / `game` |
| `recoil_input_method` | `hardware` | `hardware` / `software` |
| `recoil_require_rmb` | `false` | Require right-click |
| `recoil_randomisation` | `false` | Enable jitter |
| `recoil_random_strength` | `5.0` | Jitter scale |
| `recoil_x_control` | `100` | Global X % |
| `recoil_y_control` | `100` | Global Y % |
| `active_game` | `cs2` | Active game id |
| `recoil_game_settings` | object | Weapon + sensitivity |
| `recoil_simple_settings` | object | X, Y, delay |
| `recoil_advanced_settings` | object | Pattern + loop |

---

## AI keys (selection)

| Key | Default | Description |
|-----|---------|-------------|
| `ai_engine_enabled` | `false` | AI master switch |
| `ai_active_model` | `""` | Model filename |
| `ai_inference_backend` | `cuda_ultralytics` | Backend id |
| `ai_capture_mode` | `ndi` | `ndi` / `mss` |
| `ai_ndi_source` | `""` | NDI source name |
| `ai_main_pc_width` | `1920` | Gaming display width |
| `ai_main_pc_height` | `1080` | Gaming display height |
| `ai_detection_conf` | `0.25` | Detection threshold |
| `ai_imgsz` | `640` | Input size |
| `ai_max_detect` | `50` | Max detections |
| `ai_aim_mode` | `normal` | `normal` / `bezier` / `silent` |
| `ai_aim_keybind` | `rmb` | Aim hold key |
| `ai_always_on_aim` | `false` | Always aim |
| `ai_trigger_always_on` | `false` | Always trigger |

Full defaults are in `Config/config_manager.py` (`DEFAULTS` + `AI_DEFAULTS`).

---

## AI profile files

Aim `.cfg` files: `%APPDATA%\AimSync\bin\configs\`

Models: `%APPDATA%\AimSync\bin\models\`
