# FAQ

---

**What is AimSync?**
A local web app for Makcu HID recoil control, pattern editing, and optional AI aim/trigger on a dual-PC setup.

**Do I need two PCs?**
No for basic recoil. **Yes** for NDI-based AI capture from a gaming PC while AimSync runs on a second PC with Makcu.

**Why venv instead of `.exe`?**
PyTorch + CUDA + Makcu are more reliable with native pip than a frozen bundle. See [Venv distribution](Venv-Distribution).

**Where do models come from?**
Place `.onnx` / `.pt` files in `%APPDATA%\AimSync\bin\models\`. No public model store — bring your own weights.

**Is the AI always on?**
No — use **Start AI engine** in the UI. Optional always-on aim/trigger in AI settings.

**Can I build from GitHub clone alone?**
The public repo may not include all protected core files. Use a [Release](https://github.com/Kava4/AimSync/releases) or full source zip from the maintainer.

**Is it free?**
Current access mode is free. Licensing hooks are placeholders.

**Does this work without Makcu?**
Software input exists for testing; hardware mode is the intended production path.

**Where is documentation?**
This wiki. Repo `README.md` links here.

---

[Installation](Installation) · [Troubleshooting](Troubleshooting) · [Ko-fi](https://ko-fi.com/kava4)
