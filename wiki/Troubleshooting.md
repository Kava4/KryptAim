# Troubleshooting

---

## Install & startup

| Symptom | Fix |
|---------|-----|
| Python not found (venv path) | Install Python 3.10+ with **Add to PATH**, or use slim exe |
| `install_kryptaim_pc.bat` fails | Read error; run `repair_ai_deps.bat` after NVIDIA driver |
| Port 5000 in use | Close other AimSync instances |
| Dashboard won't open | Check firewall; use `http://127.0.0.1:5000` |

---

## Slim exe / AI runtime bootstrap

| Symptom | Fix |
|---------|-----|
| "AI components not installed" banner | AI tab → **Install AI runtime** |
| Install stuck / failed | Internet required; allow python.org + pypi.org |
| AI still unavailable after install | **Restart** `AimSync.exe` |
| Retry clean install | Delete `%APPDATA%\AimSync\runtime\` and install again |
| CUDA torch install failed | CPU ONNX may work; update NVIDIA driver and retry |
| Embed download fails | Falls back to system Python if `py -3.12` is installed |

Log: `%APPDATA%\AimSync\aimsync.log`

---

## Makcu

| Symptom | Fix |
|---------|-----|
| Disconnected | USB cable, driver, close other Makcu tools |
| No movement | Input method = **Hardware**; master switch on |
| Wrong mouse buttons | Only one app may hold Makcu COM port |

---

## AI / CUDA

| Symptom | Fix |
|---------|-----|
| AI tab errors on load | `install_kryptaim_pc.bat` |
| `torch.cuda` false | `repair_ai_deps.bat` (close AimSync first) |
| CPU inference ~8 fps | Need `CUDAExecutionProvider` — repair deps + driver |
| Model load timeout | Check `aimsyc_debug.log`; verify `.onnx` in `bin/models/` |
| Model fails | Use YOLOv8 `.onnx` / `.pt`; re-run install |

---

## NDI

| Symptom | Fix |
|---------|-----|
| No NDI sources | Install NDI Runtime on **both** PCs |
| cyndilib missing | Re-run `install_kryptaim_pc.bat` |
| Native module error | `kryptaim-venv\Scripts\python.exe scripts\diagnose_ndi.py` |
| Frozen exe NDI broken | Rebuild with `create_build_venv.bat` + `build_app.bat` |

---

## Recoil

| Symptom | Fix |
|---------|-----|
| No compensation | Master on + hotkey held + correct mode |
| Pattern wrong scale | Match CS2 sensitivity in Game Engine |
| Cloud empty | Normal — upload via Share first |

---

## Logs

```
%APPDATA%\AimSync\aimsyc_debug.log
```

Verify stack:

```bat
kryptaim-venv\Scripts\python.exe scripts\verify_build_ai_stack.py
```
