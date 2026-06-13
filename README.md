# AimSync for Makcu — Dual-PC CS2 Recoil & AI

**AimSync** is a Windows app built for **[Makcu](https://www.makcu.com/) HID** users running **Counter-Strike 2** on a dual-PC setup. Your game PC sends video over **NDI**; your AimSync PC runs recoil control (and optional YOLO AI) and moves the **gaming mouse through Makcu hardware** — not software simulation on the game PC.

> **Download:** [Latest release (AimSync.exe)](https://github.com/AimSyncCore/AimSync/releases/latest) — no Python required on the AimSync PC.

## Why Makcu + AimSync?

| | |
|---|---|
| **Hardware input** | Mouse movement goes through Makcu USB HID — the path anti-cheat sees as a real device |
| **Dual-PC** | CS2 stays clean on the game PC; GPU, NDI, and Makcu live on the AimSync PC |
| **Recoil** | 12 CS2 weapons, CT/T picker, sensitivity scaling, randomisation, return-to-crosshair |
| **AI (optional)** | YOLO over NDI — aim assist, trigger, team filter, community ONNX models |
| **Dashboard** | Dark web UI at `http://<local-ip>:5000` — configure from phone or second monitor |
| **Portable** | ~17 MB lite `.exe` — recoil works immediately; AI runtime installs to AppData on first use |

## Quick start (exe)

1. Download **`AimSync.exe`** from [Releases](https://github.com/AimSyncCore/AimSync/releases/latest)
2. Connect **Makcu** to the AimSync PC (and to your game setup per your wiring)
3. Run the exe → open the dashboard URL shown in the tray / console
4. **Game Engine** tab → pick weapon & sensitivity · **AimSync AI** tab → NDI source + model (optional)

Config: `%APPDATA%\AimSync\config.json`

## Run from source (developers)

```bat
scripts\install_aimsync_pc.bat   :: first time
scripts\run.bat                  :: production Makcu
scripts\run_dev.bat              :: simulated Makcu + dev keys
```

Tests: `python -m pytest tests/`

## Dual-PC wiring (typical)

```text
[Gaming PC]  CS2 + NDI out
      │
      ▼  (network)
[AimSync PC]  AimSync + Makcu
      │
      ▼  (USB HID)
[Gaming mouse on game PC]
```

## What's in this repo

| Path | Public? | Notes |
|------|---------|-------|
| `app/` | ✅ | Core engine — sensitive logic shipped as sealed blobs |
| `app/protected/sealed/` | ✅ | Encrypted modules (recoil, AI, licensing) |
| `app/_src/` | ❌ | Maintainer plaintext (gitignored) |
| `web/` | ✅ | Flask UI |
| `scripts/` | ✅ | Run, install, build, seal (dev asset scripts gitignored) |
| `tests/` | ✅ | Pytest suite |
| `wiki/` | ✅ | User & dev docs |
| `release/` | ✅ | `version.json`, remote feature flags |
| `dist/` | ❌ | Use GitHub Releases for the `.exe` |

## Build your own exe

```bat
scripts\create_build_venv.bat
scripts\build_app.bat
scripts\package_release.bat
```

Lite profile (~50–120 MB build) · Full offline: `scripts\build_app_full.bat`

## Other AimSync projects

In-app **Projects** page or see [`release/projects.json`](release/projects.json) — WebRadar, Crosshair Studio, Logitech recoil script, and more.

## Support

- **Ko-fi:** [ko-fi.com/kava4](https://ko-fi.com/kava4)
- **PayPal:** [paypal.me/kava4](https://paypal.me/kava4)
- In-app **Feedback** / **Support** (GiftMeCrypto & Paysafe codes → Discord)

## License

Early Access · see repository license file. Community models: AimSync catalog + filtered [Aimmy CS2 models](https://github.com/Babyhamsta/Aimmy/tree/Aimmy-V2/models).
