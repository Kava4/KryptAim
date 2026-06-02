# Local API reference

The AimSync desktop app exposes a Flask server on port **5000**. Replace `{host}` with your LAN IP or `127.0.0.1`.

**Base URL:** `http://{host}:5000`

Most UI actions use `POST` with `application/x-www-form-urlencoded` bodies. License endpoints accept JSON from server-side proxies.

---

## Pages

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Main dashboard (HTML) |

---

## Application

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/quit` | Stop AimSync |
| POST | `/api/shutdown_computer` | Stop app and shutdown PC |
| POST | `/api/feedback` | Forward feedback to Cloud → Discord |

---

## License (implemented in `Server/app.py`)

| Method | Path | Body | Description |
|--------|------|------|-------------|
| GET | `/api/recoil/license_status` | — | Poll trial/premium HTML fragment |
| POST | `/api/recoil/validate_license` | form: `license_key`, `activate_trial` | Apply key or start trial |

---

## Recoil control (`/api/recoil/...`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/toggle` | Master switch |
| POST | `/mode` | `recoil_mode`: `simple`, `advanced`, `CS2` |
| POST | `/keybind` | Master keybind |
| POST | `/cycle_keybind` | Weapon cycle key |
| POST | `/require_rmb` | Require RMB |
| POST | `/input_method` | `hardware` / `software` |
| GET | `/status` | Status HTML fragment |
| GET | `/hardware-check` | Makcu connection HTML |
| GET | `/current_weapon` | Active weapon name (plain text) |

### Safety

| Method | Path |
|--------|------|
| POST | `/safety_features_toggle` |
| POST | `/randomisation` |
| POST | `/random_strength` |
| POST | `/x_control`, `/y_control`, `/speed_control` |

### Simple mode

| Method | Path |
|--------|------|
| POST | `/x`, `/y`, `/delay` |

### Advanced / Recoil Lab

| Method | Path |
|--------|------|
| POST | `/advanced_pattern` |
| POST | `/loop` |
| POST | `/pattern/save`, `/pattern/load`, `/pattern/delete` |

### Game Engine (premium)

| Method | Path | Notes |
|--------|------|-------|
| GET/POST | `/cs2_weapon` | Donator required on POST |
| POST | `/cs2_sensitivity` | Donator required |
| POST | `/game_weapon` | Active game weapon |
| POST | `/game_sensitivity` | Sensitivity scale |
| POST | `/game_loop` | Pattern loop |
| POST | `/active_game` | Switch game id |

### Cloud proxy (premium upload)

| Method | Path |
|--------|------|
| GET | `/cloud/list` |
| POST | `/cloud/upload` |
| GET | `/cloud/load?name=` |
| POST | `/cloud_username` |

---

## Game routes (`Server/app.py`)

| Method | Path |
|--------|------|
| POST | `/api/recoil/game_weapon` |
| POST | `/api/recoil/game_sensitivity` |
| POST | `/api/recoil/game_loop` |
| POST | `/api/recoil/active_game` |
| POST | `/api/recoil/cycle_keybind` |
| POST | `/api/recoil/shutdown_on_exit_toggle` |
| POST | `/api/recoil/safety_features_toggle` |

---

## Example: toggle master switch

```bash
curl -X POST http://127.0.0.1:5000/api/recoil/toggle \
  -d "recoil_enabled=on"
```

## Example: validate trial (via local proxy)

```bash
curl -X POST http://127.0.0.1:5000/api/recoil/validate_license \
  -d "license_key=FREETRIAL&activate_trial=true"
```

## See also

- [Cloud API](cloud-api.md)
