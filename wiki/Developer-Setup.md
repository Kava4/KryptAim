# Developer setup

Clone [Kava4/KryptAim](https://github.com/Kava4/KryptAim) (branch **Beta**).

---

## Prerequisites

- Windows 10/11
- Python 3.10+ (3.12 recommended)
- Makcu device (hardware tests)
- NVIDIA GPU (AI tests)

---

## Run from source

```bat
scripts\install_kryptaim_pc.bat
scripts\run_dev.bat
```

Production (Makcu):

```bat
scripts\run.bat
```

Tests:

```bat
.venv\Scripts\python.exe -m pytest tests\
```

Config & logs: `%APPDATA%\KryptAim\`

---

## Project layout

See [Architecture](Architecture).

---

## Build exe (maintainer)

**Lite** (default — ~15–120 MB, AI via AppData bootstrap):

```bat
scripts\create_build_venv.bat
scripts\build_app.bat
scripts\package_release.bat
```

**Full** (offline — ~2–4 GB, AI bundled):

```bat
scripts\create_build_venv.bat
scripts\build_app_full.bat
```

Debug console build: `scripts\build_debug.bat`

Output: `dist\KryptAim.exe` (lite) or `dist\KryptAim\` (full onedir)

Bootstrap: `app/bootstrap/embed_python.py`, `app/bootstrap/runtime.py`

---

## Publish release

1. Bump `release/version.json`
2. Build + `scripts\package_release.bat`
3. Create GitHub Release on [Kava4/KryptAim](https://github.com/Kava4/KryptAim/releases) with tag `vX.Y.Z`
4. Attach `KryptAim.exe` or `KryptAim.zip`
5. Push `release/app-config.json` if changing remote flags (e.g. AI premium gate)

Wiki auto-syncs from `wiki/` on push (see `.github/workflows/wiki-sync.yml`).

---

## Related

- [Architecture](Architecture)
- [Local API](Local-API)
