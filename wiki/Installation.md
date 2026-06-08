# Installation

AimSync runs on **Windows 10/11**. The recommended path is a **Python venv** on the AimSync PC (GPU + Makcu + NDI).

---

## Requirements

| Component | AimSync PC | Gaming PC |
|-----------|------------|-----------|
| Windows 10/11 | Yes | Yes |
| Python 3.10+ | Yes | No |
| NVIDIA GPU + driver | Yes (AI) | Optional |
| [CUDA 12.6](https://developer.nvidia.com/cuda-12-6-0-download-archive) | Yes (AI) | No |
| [NDI Runtime](https://ndi.link/NDIRedistV6) | Yes | Yes |
| Makcu HID device | Yes | Mouse via Makcu |

---

## Install (venv — recommended)

1. Copy the full AimSync folder to the AimSync PC (or extract `AimSync-PC.zip`).
2. Run once:

```bat
scripts\install_aimsync_pc.bat
```

3. Every session:

```bat
scripts\run_aimsync.bat
```

4. Open `http://<local-ip>:5000` in your browser.

The install script:
- Creates `aimsync-venv`
- Installs `requirements-aimsync-pc.txt`
- Installs PyTorch **CUDA 12.6** wheels
- Runs `scripts\verify_build_ai_stack.py`

---

## Models

Place YOLO models in:

```
%APPDATA%\AimSync\bin\models\
```

Example: `cs2_640.onnx`

You can also upload models via the **AI** tab in the dashboard.

---

## Portable `.exe` (optional)

If you have a PyInstaller build from a maintainer:

1. Extract `dist\AimSync\` anywhere.
2. Run `AimSync.exe`.
3. Data still lives under `%APPDATA%\AimSync\`.

Legacy `%APPDATA%\AimSyncBeta\` is read if `AimSync\config.json` is missing.

---

## Repair CUDA / torch

If AI shows CPU inference or `torch.cuda` is false:

```bat
scripts\repair_ai_deps.bat
```

Close AimSync first (`scripts\stop_all.bat`).

---

## Next steps

- [Quick Start](Quick-Start)
- [Dual-PC CS2 test](Dual-PC-CS2)
- [Troubleshooting](Troubleshooting)
