# Quick Start

Five-minute checklist after [Installation](Installation).

---

## 1. Hardware

1. Connect **Makcu** to the AimSync PC.
2. Connect the gaming mouse through Makcu (dual-PC setup).
3. Install **NDI Runtime** on both PCs.

---

## 2. Launch

```bat
scripts\run_aimsync.bat
```

Open the dashboard: `http://<LAN-IP>:5000`

Check **Global Settings** → Makcu status should show **Connected**.

---

## 3. Basic recoil

1. **Global Settings** → enable master switch.
2. Set hotkey (default **M4**).
3. **Simple Recoil** or **Recoil Lab** → tune X/Y.
4. **Recoil** tab → Input method: **Hardware (Makcu)**.

---

## 4. CS2 Game Engine

1. Open **Game Engine** (CS2).
2. Select weapon (e.g. AK-47).
3. Set in-game sensitivity to match your CS2 settings.
4. Test in-game with hotkey held.

---

## 5. AI Engine (dual-PC)

1. Gaming PC: NDI output (OBS / NDI Screen Capture).
2. AimSync PC: **AI** tab → Refresh NDI sources → pick stream.
3. Select model (`cs2_640.onnx` in `%APPDATA%\AimSync\bin\models\`).
4. Click **Start AI engine**.
5. Set main PC resolution (e.g. 1920×1080).

See [Dual-PC CS2](Dual-PC-CS2) for full test steps.

---

## Scripts cheat sheet

| Task | Command |
|------|---------|
| Install once | `scripts\install_aimsync_pc.bat` |
| Run | `scripts\run_aimsync.bat` |
| Dev run | `scripts\run_dev.bat` |
| Stop all | `scripts\stop_all.bat` |
| Fix CUDA | `scripts\repair_ai_deps.bat` |
| Verify stack | `aimsync-venv\Scripts\python.exe scripts\verify_build_ai_stack.py` |
| NDI diagnose | `aimsync-venv\Scripts\python.exe scripts\diagnose_ndi.py` |
