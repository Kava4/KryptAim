# Installation

## Who this guide is for

Most users should install AimSync from an **official release**, not from the public GitHub source tree. The repository is intentionally incomplete: core engine and hardware logic are withheld so the project cannot be copied or rebuilt in full from Git alone.

---

## Recommended: official release (Windows)

1. Open [GitHub Releases](https://github.com/Kava4/AimSync/releases/latest).
2. Download **`AimSync.exe`** (single portable executable).
3. Run it on **Windows 10/11** (any folder you prefer).
4. On first launch, the dashboard opens in your browser at `http://<local-ip>:5000`.

There is no `_internal` folder to ship — the app unpacks bundled assets to a temporary directory at runtime.

### Where release builds store data

| Data | Location |
|------|----------|
| Settings | `%APPDATA%\AimSync\config.json` |
| Saved patterns | `%APPDATA%\AimSync\saved_patterns\` |
| Debug log | `aimsyc_debug.log` next to `AimSync.exe` (when enabled) |

This is the only supported path for players and supporters who want a working application.

---

## Public repository vs full application

The [public GitHub repository](https://github.com/Kava4/AimSync) is an **open-facing slice** of the project. It is useful for documentation, issues, discussions, and transparency around the UI and cloud integration—but it is **not** a complete, buildable copy of AimSync.

### Included in the public repo (typical)

| Area | Examples |
|------|----------|
| Desktop shell | `main.py`, Tkinter lifecycle, thread startup |
| Web dashboard | `Server/app.py`, templates, static assets |
| Configuration | `Config/config_manager.py`, defaults |
| Game data (profiles) | `Recoil/games/*.py` weapon coordinate modules |
| Pattern Generator | `PatternGenerator/` (standalone tooling) |
| Documentation | `docs/` wiki |
| Tests | `tests/` (limited; hardware tests need Makcu) |

### Withheld from the public repo (by design)

These paths are listed in `.gitignore` and are **not published** to prevent redistribution of proprietary logic:

| Path | Role |
|------|------|
| `Recoil/recoil.py` | Main recoil execution loop |
| `Makcu/makcu_manager.py` | Makcu HID connection and hardware movement |
| `Server/cloud_manager.py` | License validation client and premium cache |
| `Server/routes/` | HTMX API route handlers (`recoil_routes.py`, etc.) |
| `build_app.py`, `build_app.bat`, `AimSync.spec` | Release packaging scripts |

Optional local paths (git-ignored if present): `**/*_source.py`, `PatternExtractor/`, `Menu/`.

Also excluded: `config.json`, `venv/`, `dist/`.

### Why files are withheld

AimSync’s value includes tuned recoil engines, hardware integration, and license enforcement. Publishing only the dashboard and docs while keeping the engine private:

- Reduces straight cloning of paid functionality  
- Keeps one official build channel (signed releases)  
- Still allows community input via docs, feedback, and pattern discussion  

This is a deliberate **source-available UI + docs** model, not “clone and run everything.”

---

## What happens if you clone and run from GitHub

A minimal clone plus `pip install -r requirements.txt` and `python main.py` will **not** produce a working app for end users. Python will typically fail with **import errors** because modules such as:

- `Recoil.recoil`
- `Makcu.makcu_manager`
- `Server.cloud_manager`
- `Server.routes.recoil_routes`

are missing from the public tree.

That behavior is expected, not a broken install on your side.

---

## Requirements (release build)

| Component | Requirement |
|-----------|-------------|
| Operating system | Windows 10/11 (primary target) |
| Browser | Chromium, Firefox, or Edge |
| Hardware (optional) | Makcu device for **hardware** input mode |
| Network | Internet for license / trial and cloud patterns (optional) |

Python is **not** required when using the packaged `.exe`—only for maintainers with a full internal tree.

---

## Verify Makcu (hardware mode)

1. Connect the Makcu device before launching AimSync.
2. Open **Global Settings** → set **Input method** to **Hardware**.
3. Watch the hardware status indicator (polls `/api/recoil/hardware-check`).

If no device is found at startup, the app may run in **management-only mode** (dashboard works; hardware movement does not) until you reconnect and restart.

---

## Building from source

**End users:** use [Releases](https://github.com/Kava4/AimSync/releases/latest). There is no supported public “build from GitHub” workflow.

**Maintainers:** packaging uses private scripts (`build_app.py`, PyInstaller spec) that are not in the public repository. Builds are produced internally and published as release artifacts.

For more detail, see [Developer setup](../development/setup.md) → *Public clone limitations*.

---

## Next steps

- [Quick start](quick-start.md) — trial, master switch, first profile  
- [Application overview](../user-guide/overview.md)  
- [Troubleshooting](../support/troubleshooting.md) — includes “missing module” after a Git clone  
