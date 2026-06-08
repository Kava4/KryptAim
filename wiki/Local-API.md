# Local API

Flask HTTP API on port **5000**. Base URL: `http://<host>:5000`

Most UI actions use `POST` with form fields and return JSON `{ "success": true/false }`.

---

## Recoil — `/api/recoil`

| Route | Method | Purpose |
|-------|--------|---------|
| `/status` | GET | App + license status |
| `/hardware_check` | GET | Makcu connection |
| `/toggle` | POST | Enable/disable recoil |
| `/hotkeys` | GET/POST | Hotkey config |
| `/input_method` | POST | hardware / software |
| `/randomisation` | POST | Safety toggles |
| `/x_control`, `/y_control`, `/speed_control` | POST | Global multipliers |
| `/x_setting`, `/y_setting`, `/delay_setting` | POST | Simple recoil |
| `/advanced_pattern` | POST | Advanced pattern data |
| `/cs2_weapon`, `/cs2_sensitivity` | POST | Game engine |
| `/save_pattern`, `/load_pattern`, `/delete_pattern` | POST | Pattern library |
| `/cloud_list`, `/cloud_upload`, `/cloud_load` | GET/POST | Community patterns |

---

## AI — `/api/ai`

| Route | Method | Purpose |
|-------|--------|---------|
| `/status` | GET | Engine status, readiness |
| `/settings` | GET | Current AI settings |
| `/enable` | POST | Start/stop engine |
| `/quickstart` | POST | One-click setup |
| `/model/select` | POST | Load model |
| `/inference_backend` | POST | Backend selection |
| `/capture` | POST | Capture mode / NDI |
| `/ndi/refresh` | GET | List NDI sources |
| `/detection` | POST | Conf, imgsz, max detect |
| `/profiles/list`, `/save`, `/load` | GET/POST | AI profiles |
| `/config/upload`, `/select`, `/save` | POST | `.cfg` files |
| `/debug/frame` | GET | Debug frame (if enabled) |

---

## Pattern Generator — `/api/pattern-generator`

| Route | Method | Purpose |
|-------|--------|---------|
| `/weapons/<game_id>` | GET | Weapon list |
| `/detect` | POST | Upload image/GIF |
| `/detect-url` | POST | Remote URL |
| `/preview` | POST | Preview pattern |
| `/append` | POST | Write to game file |

---

## Notes

- AI routes return 503/504 on model load timeout — check `aimsyc_debug.log`.
- CORS is local-only; do not expose port 5000 to the public internet.
