# Dual-PC CS2 test

Two PCs:
- **Gaming PC** — CS2 + NDI video out
- **AimSync PC** — AimSync + Makcu + NVIDIA GPU + AI

No separate helper app on the gaming PC.

---

## AimSync PC — one-time

```bat
scripts\install_aimsync_pc.bat
```

Install [NDI Runtime](https://ndi.link/NDIRedistV6) and [CUDA 12.6](https://developer.nvidia.com/cuda-12-6-0-download-archive).

Put model in `%APPDATA%\AimSync\bin\models\` (e.g. `cs2_640.onnx`).

Verify:

```bat
aimsync-venv\Scripts\python.exe scripts\verify_build_ai_stack.py
aimsync-venv\Scripts\python.exe scripts\diagnose_ndi.py
```

---

## Every session

```bat
scripts\run_aimsync.bat
```

### Web UI checklist

1. **Recoil** → Input method: **Hardware (Makcu)**.
2. **AI** tab:
   - Model: `cs2_640.onnx`
   - Capture: **NDI** → refresh sources → pick gaming stream
   - Main PC resolution: e.g. **1920×1080**
   - **Start AI engine**
3. Makcu: **Connected**.

Aim/trigger keys (e.g. **RMB**) are read from the gaming mouse via Makcu on the AimSync PC — same path as recoil.

Optional: **Always-on aim** / **Trigger always on** in the AI panel.

---

## Gaming PC

1. Install NDI Runtime.
2. Enable NDI output:
   - OBS → Tools → NDI Output, or
   - NDI Screen Capture
3. Run CS2 fullscreen/windowed as usual.

---

## Test procedure

1. **Recoil** — fire in CS2; crosshair compensation moves via Makcu.
2. **AI** — enable engine; check detections / OpenCV debug window if enabled.
3. **Logs** — `%APPDATA%\AimSync\aimsyc_debug.log`

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No NDI sources | NDI Runtime on both PCs; refresh sources in AI tab |
| cyndilib missing | Re-run `install_aimsync_pc.bat` |
| CPU inference | `repair_ai_deps.bat` + NVIDIA driver |
| Makcu in use | Close other tools; only AimSync may hold the device |

See [Troubleshooting](Troubleshooting) and [AI Engine](AI-Engine).
