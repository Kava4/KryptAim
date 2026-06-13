# AimSync

Dual-PC CS2 desktop app — Makcu HID, spray recoil, YOLO aim engine over NDI.

Product name: **AimSync** (`BRAND.md`). Legacy monolith archived in `.backup-legacy/`.

## Run

**Dev (no Makcu):**

```bat
scripts\run_dev.bat
```

**First time on AimSync PC:**

```bat
scripts\install_aimsync_pc.bat
```

**Production (Makcu):**

```bat
scripts\run.bat
```

Opens `http://<local-ip>:5000` in your browser. Config: `%APPDATA%\AimSync\config.json`.

If you see `No Python at ...Python312...`, delete `.venv` or re-run `run.bat`.

Tests: `python -m pytest tests/`

**AimSync PC (AI):** `scripts\repair_ai_deps.bat` then `python scripts\diagnose_ndi.py`

## Distribution (.exe)

Two build profiles:

| Profile | Script | Size | AI stack |
|---------|--------|------|----------|
| **lite** (default) | `scripts\build_app.bat` | ~50–120 MB | Installs to `%APPDATA%\AimSync\runtime` on first use (button in AI tab) |
| **full** | `scripts\build_app_full.bat` | ~2–4 GB | Everything bundled offline |

**Lite flow:** Ship small `AimSync.exe` → recoil works immediately → AI tab → **Install AI runtime** (embeddable Python + pip to AppData, no system Python).

**Full flow:** Fat build for offline USB — everything bundled, no first-run install.

Build machine setup:

```bat
scripts\create_build_venv.bat
scripts\build_app.bat
scripts\package_release.bat
```

Output: `dist\AimSync.exe` (lite, single file) or `dist\AimSync\` (full onedir + `_internal`)

Debug build (console): `scripts\build_debug.bat`

## Layout

```text
AimSync/
├── app/           # core, makcu, ai, recoil, bootstrap, web runner
├── web/           # Flask UI (templates + static)
├── website/       # React marketing site (GitHub Pages)
├── scripts/
├── tests/
├── wiki/
├── release/       # version.json, app-config.json
└── main.py
```

See `wiki/` on [AimSyncCore/AimSync](https://github.com/AimSyncCore/AimSync/wiki) for more.
