# AI Engine

YOLO-based detection, aim assist, and triggerbot. Runs on the **KryptAim PC** with Makcu movement.

**Access:** Free by default. Premium gate is optional via `release/app-config.json` on GitHub.

---

## Pipeline

```
NDI capture → YOLO inference → CT/T class filter → aim/trigger → Makcu
```

| Stage | Module | Notes |
|-------|--------|-------|
| Capture | `app/ai/capture*.py` | NDI (dual-PC) |
| Inference | `app/ai/inference.py` | Ultralytics + ONNX |
| Classes | `app/ai/class_names.py` | CT/T from model metadata |
| Targeting | `app/ai/targets.py` | Enemy class + aim point |
| Engine | `app/ai/engine.py` | Main loop |

---

## Setup (dual-PC)

1. Gaming PC: NDI output enabled.
2. KryptAim PC: CUDA driver + NDI Runtime.
3. **Slim exe:** Global Settings → **AI Runtime** → install once. Restart when done.
4. AI tab:
   - Select **NDI source**
   - **Community models** or upload `.onnx` / `.pt`
   - Pick **your team (CT/T)** — targets enemy class automatically
   - **Quick setup** → **Start AI engine**

---

## Key settings (`config.json`)

| Key | Purpose |
|-----|---------|
| `ai_enabled` | Master AI on/off |
| `ai_model_path` | Path to weights |
| `ai_my_team` | `ct` or `t` — auto enemy class |
| `ai_player_class` | Manual body class override |
| `ai_head_class` | Head class if model has one |
| `ai_capture_mode` | `ndi` |
| `ai_ndi_source` | NDI stream name |
| `ai_detection_conf` | Confidence threshold |
| `ai_aim_enabled` / `ai_trigger_enabled` | Feature toggles |

---

## Community models

Sources (no Vercel catalog):

- **Kava4/KryptAim** `models/` on GitHub
- **Aimmy** CS2 models (`Babyhamsta/Aimmy`, branch `Aimmy-V2`)

Saved to `%APPDATA%\KryptAim\models\`.

---

## Debug

- Log: `%APPDATA%\KryptAim\aimsync.log`
- Runtime install log: `%APPDATA%\KryptAim\runtime\install.log`

---

## Related

- [Dual-PC CS2](Dual-PC-CS2)
- [Configuration](Configuration)
- [Local API](Local-API) — `/api/ai/*`
- [Cloud API](Cloud-API) — remote flags
