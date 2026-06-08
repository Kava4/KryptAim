# Developer setup

For contributors with the **full source tree**.

---

## Prerequisites

- Windows 10/11
- Python 3.10+
- Makcu device (for hardware tests)
- NVIDIA GPU (for AI tests)

---

## Run from source

```bat
scripts\install_aimsync_pc.bat
scripts\run_dev.bat
```

Dev data directory: `<project>/.aimsync-data/`

Tests:

```bat
aimsync-venv\Scripts\python.exe -m pytest tests\
```

---

## Project layout

```
AimSync/
├── main.py              # Entry point
├── Config/              # config.json, app identity
├── Makcu/               # HID manager
├── Recoil/              # Recoil engine + games/
├── AI/Engine/           # Capture, inference, aim, trigger
├── Server/              # Flask app, routes, templates
├── PatternGenerator/    # Standalone GIF/image tool
├── scripts/             # Install, run, build helpers
└── tests/
```

---

## Build exe (maintainer)

```bat
scripts\create_build_venv.bat
scripts\build_app.bat
```

Debug console build:

```bat
scripts\build_debug.bat
```

Output: `dist\AimSync\`

`build_app.py` and `.spec` may be gitignored — maintainer-only.

---

## Package venv release

```bat
scripts\package_aimsync_pc_release.bat
```

---

## Source backup export

```bat
python scripts\export_clean_source_txt.py
```

Creates `AimSync_CLEAN_SOURCE.txt` (gitignored).

---

## Related

- [Architecture](Architecture)
- [Local API](Local-API)
