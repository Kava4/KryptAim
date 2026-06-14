# Installation

KryptAim runs on **Windows 10/11**. Use either **venv + source** (developers) or **slim `.exe`** (end users).

Repository: [AimSyncCore/KryptAim](https://github.com/AimSyncCore/KryptAim)

---

## Requirements

| Component | KryptAim PC | Gaming PC |
|-----------|------------|-----------|
| Windows 10/11 | Yes | Yes |
| Python 3.10+ | Yes (source only) | No |
| NVIDIA GPU + driver | Yes (AI) | Optional |
| [CUDA 12.6](https://developer.nvidia.com/cuda-12-6-0-download-archive) | Yes (AI) | No |
| [NDI Runtime](https://ndi.link/NDIRedistV6) | Yes | Yes |
| Makcu HID device | Yes | Mouse via Makcu |

---

## Install (venv — developers)

1. Clone the repo:

```bat
git clone -b Beta https://github.com/AimSyncCore/KryptAim.git
cd KryptAim
```

2. First-time setup:

```bat
scripts\install_kryptaim_pc.bat
```

3. Every session:

```bat
scripts\run.bat
```

Dev mode (no Makcu):

```bat
scripts\run_dev.bat
```

4. Open `http://<local-ip>:5000` in your browser.

---

## Models

Download from **AI tab → Community models** (GitHub + Aimmy CS2 catalog), or place files in:

```
%APPDATA%\KryptAim\models\
```

Supported: `.onnx`, `.pt`, `.engine`

---

## Slim `.exe` (recommended for end users)

Download from [Releases](https://github.com/AimSyncCore/KryptAim/releases).

1. Extract `KryptAim.exe` (single file, ~15–120 MB).
2. Run it — recoil works immediately.
3. **Global Settings → AI Runtime → Install AI runtime** (10–20 min, one-time).
4. Restart, then configure NDI + model in the **AI** tab.

Details: [Slim exe distribution](Slim-Exe-Distribution).

### Full `.exe` (offline)

Maintainers: `scripts\build_app_full.bat` — bundles AI stack (~GB), no bootstrap.

---

## Updates

**Global Settings → Updates → Check for updates** (GitHub Releases). In-app install replaces `KryptAim.exe` and restarts.

---

## Related

- [Quick Start](Quick-Start)
- [Dual-PC CS2](Dual-PC-CS2)
- [Troubleshooting](Troubleshooting)
