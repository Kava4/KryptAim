# AI Engine

YOLO-based detection, aim assist, and triggerbot. Runs on the **AimSync PC** with Makcu movement.

---

## Pipeline overview

```
NDI / MSS capture → YOLO inference → target selection → aim/trigger → Makcu movement
```

| Stage | Module | Notes |
|-------|--------|-------|
| Capture | `AI/Engine/capture*.py` | NDI (dual-PC) or MSS (local) |
| Inference | `inference_ultralytics.py` | CUDA Ultralytics (default) |
| Aim | `aim.py`, `movement/` | Normal / Bezier / Silent modes |
| Trigger | `trigger.py` | Radius + confidence + cooldown |
| Config | `.cfg` profiles | Same style as classic aim configs |

---

## Setup (dual-PC)

1. Gaming PC: NDI out.
2. AimSync PC: install CUDA + NDI + model.
3. AI tab:
   - **Inference backend**: CUDA Ultralytics
   - **Capture**: NDI → select source
   - **Model**: `.onnx` / `.pt` in `bin/models/`
   - **Main PC resolution**: match gaming display
4. **Start AI engine**

Quick setup: use the built-in quickstart API (`POST /api/ai/quickstart`) from the UI.

---

## Key settings

| Setting | Purpose |
|---------|---------|
| `ai_engine_enabled` | Master AI on/off |
| `ai_active_model` | YOLO weights filename |
| `ai_capture_mode` | `ndi` or `mss` |
| `ai_ndi_source` | NDI stream name |
| `ai_inference_backend` | `cuda_ultralytics` (recommended) |
| `ai_detection_conf` | Confidence threshold |
| `ai_imgsz` | Model input size (640 typical) |
| `ai_max_detect` | Max boxes per frame |
| `ai_always_on_aim` | Aim without hold key |
| `ai_trigger_always_on` | Trigger without hold key |

---

## Debug

- Enable **OpenCV window** in Capture settings for live preview (local window only).
- Log file: `%APPDATA%\AimSync\aimsyc_debug.log`

---

## Related

- [Dual-PC CS2](Dual-PC-CS2)
- [Configuration](Configuration) — `ai_*` keys
- [Local API](Local-API) — `/api/ai/*`
