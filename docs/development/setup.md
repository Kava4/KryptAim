# Developer setup

This page is for people working on AimSync with a **full source tree**. If you only cloned the public GitHub repository, read [Installation → Public repository vs full application](../getting-started/installation.md) first.

---

## Public clone limitations

The public repo is **not** sufficient to run or build the shipping product. After `git clone`, you will be missing gitignored modules that the application imports at runtime.

| Missing from public Git | Imported by |
|-------------------------|-------------|
| `Recoil/recoil.py` | `main.py` |
| `Makcu/makcu_manager.py` | `main.py`, routes, engine |
| `Server/cloud_manager.py` | `Server/app.py`, routes |
| `Server/routes/` | `Server/app.py` (`recoil_bp`) |
| `build_app.py`, `*.spec` | Release pipeline |

Attempting `python main.py` without these files results in `ModuleNotFoundError` or similar. That is intentional.

### What you can still do with a public clone

- Read and edit documentation (`docs/`)
- Study UI templates and static assets (`Server/templates`, `Server/static`)
- Inspect game profile data (`Recoil/games/`)
- Work on Cloud API sources if present in your fork (deployment is separate; see [Cloud deployment](cloud-deployment.md))
- Run or extend **Pattern Generator** (`PatternGenerator/`) where dependencies allow

### Obtaining a full tree

| Audience | Source |
|----------|--------|
| Users | [GitHub Releases](https://github.com/Kava4/AimSync/releases/latest) only |
| Maintainers | Internal checkout with protected files restored, or extract from a release build’s bundled modules (policy is project-specific) |

Do not expect community PRs to modify `Recoil/recoil.py` or `makcu_manager.py` via the public remote—they are not accepted on GitHub by design.

---

## Prerequisites (full tree)

| Tool | Version |
|------|---------|
| Python | 3.10+ recommended |
| Git | Latest |
| Makcu device | Optional (hardware mode testing) |

---

## Install dependencies

```powershell
cd AimSync
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

---

## Run in development

```powershell
python main.py
```

Debug log: `aimsyc_debug.log` in the project root (overwritten each run).

---

## Project layout (full tree)

```
AimSync/
├── main.py
├── Config/
├── Server/
│   ├── app.py
│   ├── cloud_manager.py      # not on public Git
│   ├── routes/               # not on public Git
│   ├── templates/
│   └── static/
├── Recoil/
│   ├── recoil.py             # not on public Git
│   └── games/
├── Makcu/
│   ├── makcu_manager.py      # not on public Git
│   └── software_manager.py
├── Cloud/                    # may be private per .gitignore policy
├── PatternGenerator/
├── tests/
├── docs/
└── requirements.txt
```

---

## Tests

```powershell
.\venv\Scripts\python.exe -m pytest tests -q
```

Makcu tests require hardware or will fail on `connect()` — expected without a device.

---

## Build executable (maintainers only)

Packaging scripts are **not** published on GitHub. Maintainers use internal tooling (e.g. PyInstaller via `build_app.py` / `AimSync.spec`) to produce release binaries.

Published artifacts are uploaded to [Releases](https://github.com/Kava4/AimSync/releases/latest). End users should never need to build locally.

---

## Code style

Match existing patterns: minimal helpers, Flask + HTMX for UI, threaded background work in `main.py`.

---

## See also

- [Installation](../getting-started/installation.md)
- [Architecture](architecture.md)
- [Cloud deployment](cloud-deployment.md)
