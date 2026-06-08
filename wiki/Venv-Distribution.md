# Venv distribution

Recommended way to ship AimSync when PyInstaller bundles cause torch/Makcu issues.

---

## Maintainer: create zip

On a machine with the **full source tree** (including protected core files):

```bat
scripts\package_aimsync_pc_release.bat
```

Output:
- Folder: `release\AimSync-PC\`
- Zip: `release\AimSync-PC.zip`

The zip includes app source + `scripts/` but **not** `aimsync-venv/`, `dist/`, or `build/`.

Optional: add `release\README-AimSync-PC.txt` — copied as `README.txt` in the package.

---

## User workflow

```mermaid
flowchart LR
  A[Download zip] --> B[Extract]
  B --> C[install_aimsync_pc.bat]
  C --> D[aimsync-venv]
  D --> E[run_aimsync.bat]
  E --> F[Browser UI]
```

1. Extract zip anywhere.
2. Run `scripts\install_aimsync_pc.bat` once (needs internet for pip).
3. Run `scripts\run_aimsync.bat` every session.

---

## vs frozen `.exe`

| | venv zip | PyInstaller exe |
|---|----------|-----------------|
| Download size | Small (~MB) | Large (~GB) |
| First run | pip download | unpack only |
| torch/ultralytics | Native pip | Bundled |
| Updates | re-run install bat or `pip install -U` | Rebuild exe |

---

## Dual-PC summary

| Machine | Deliverable | Run |
|---------|-------------|-----|
| AimSync PC | `AimSync-PC.zip` | `install` → `run_aimsync` |
| Gaming PC | NDI only | Game + NDI out |

Config: `%APPDATA%\AimSync\config.json`
