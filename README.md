<p align="center">
  <img src="https://i.ibb.co/LhHngKZF/Aim-Sync-logo.png" alt="AimSync Logo" width="160" height="160" />
</p>

<h1 align="center">AimSync</h1>
<p align="center"><strong>High-integrity recoil &amp; AI for Makcu HID</strong></p>

<p align="center">
  <a href="https://github.com/Kava4/AimSync/wiki"><img src="https://img.shields.io/badge/Docs-Wiki-1f6feb?style=for-the-badge" alt="Documentation" /></a>
  <a href="https://github.com/Kava4/AimSync/releases"><img src="https://img.shields.io/badge/Releases-GitHub-24292f?style=for-the-badge&amp;logo=github" alt="Releases" /></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&amp;logo=python&amp;logoColor=white" alt="Python 3.10+" /></a>
  <a href="https://www.microsoft.com/windows"><img src="https://img.shields.io/badge/Platform-Windows-0078D4?style=for-the-badge&amp;logo=windows" alt="Windows" /></a>
</p>

<p align="center">
  <a href="https://ko-fi.com/kava4"><img src="https://img.shields.io/badge/Support-Ko--fi-F16061?style=for-the-badge&amp;logo=ko-fi&amp;logoColor=white" alt="Support on Ko-fi" /></a>
  <a href="https://paypal.me/kava4"><img src="https://img.shields.io/badge/Donate-PayPal-00457C?style=for-the-badge&amp;logo=paypal&amp;logoColor=white" alt="Donate via PayPal" /></a>
</p>

<p align="center">
  <strong>AimSync</strong> is a desktop utility for <strong>Makcu HID</strong> hardware. It runs a local web dashboard to build recoil patterns, manage CS2 weapon profiles, and drive an optional <strong>AI aim engine</strong> over a dual-PC NDI setup.
</p>

---

## Features

| Area | What you get |
|------|----------------|
| **Recoil** | Simple sliders, advanced pattern editor, CS2 game engine with sensitivity scaling |
| **Pattern Generator** | Turn spray GIFs/images into weapon data — edit, preview, append to game files |
| **Recoil Lab** | Real-time visualizer, save/load patterns, community share |
| **AI Engine** | YOLO detection, aim assist & triggerbot — NDI capture, CUDA Ultralytics |
| **Hardware** | Native Makcu integration, global hotkeys, safety randomization |

**Stack:** Python · Flask · Tailwind CSS · HTMX · HTML5 Canvas

---

## Quick start

**AimSync PC:** Windows 10/11, Python 3.10+, Makcu device.  
**AI / dual-PC:** NVIDIA GPU, [CUDA 12.6](https://developer.nvidia.com/cuda-12-6-0-download-archive), [NDI Runtime](https://ndi.link/NDIRedistV6) on both machines.

```bat
scripts\install_aimsync_pc.bat
scripts\run_aimsync.bat
```

Open **`http://<your-local-ip>:5000`** in your browser.

| Task | Command |
|------|---------|
| Repair CUDA / torch | `scripts\repair_ai_deps.bat` |
| Stop AimSync | `scripts\stop_all.bat` |
| Development | `scripts\run_dev.bat` |

Place YOLO models in `%APPDATA%\AimSync\bin\models\` (e.g. `cs2_640.onnx`).

---

## Documentation

Installation, dual-PC setup, AI tuning, API reference, and troubleshooting:

**[github.com/Kava4/AimSync/wiki](https://github.com/Kava4/AimSync/wiki)**

---

## Support

If AimSync helps your workflow, consider supporting development:

**[ko-fi.com/kava4](https://ko-fi.com/kava4)**

---

## Disclaimer

This software is intended for **educational and hardware testing** purposes. Using input automation in online multiplayer games may violate publisher terms of service. **You are responsible for how you use this software.**
