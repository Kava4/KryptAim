# Aimmy pipeline reference (AimSync Beta AI engine)

This document maps Aimmy-Makcu modules to AimSync `AI/Engine/` for maintenance and parity checks.

## Pipeline flow

1. **Input** — Aim keybinds held (or Constant AI Tracking).
2. **Capture** — Crop `IMAGE_SIZE` region at screen center or mouse (`capture.py` / `CaptureManager.cs`).
3. **Preprocess** — RGB → NCHW float32 ÷ 255 (`inference.py` / `BitmapToFloatArrayInPlace`).
4. **Inference** — ONNX YOLOv8 via DirectML or CPU (`inference.py` / `AIManager.LoadModelAsync`).
5. **Filter** — Min confidence + FOV rectangle mask (`target.py` / `PrepareKDTreeData`).
6. **Select** — Nearest detection to center; optional sticky aim (`target.py` / `HandleStickyAim`).
7. **Trigger** — Auto click / spray via Makcu (`trigger.py` / `AutoTrigger`, `DoTriggerClick`).
8. **Aim** — Relative move via Makcu (`aim.py` / `MoveCrosshair`).

## File mapping

| Aimmy | AimSync |
|-------|---------|
| `Dictionary.cs` | `AI/Engine/settings.py` |
| `SaveDictionary.cs` | `settings.load_cfg` / `save_cfg` |
| `FileManager.cs` | `AI/Engine/models.py` |
| `CaptureManager.cs` | `AI/Engine/capture.py` |
| `AIManager.cs` | `AI/Engine/engine.py`, `inference.py`, `target.py` |
| `MouseManager.cs` | `AI/Engine/trigger.py`, `aim.py`, `Makcu/makcu_manager.py` |
| `HandlePredictions` | `AI/Engine/prediction.py` (phase 2, `ai_phase >= 2`) |

## Data paths (beta only)

- Models: `{get_base_dir()}/bin/models/*.onnx`
- Configs: `{get_base_dir()}/bin/configs/*.cfg`

Dev beta uses `.beta-data/`; release beta uses `%APPDATA%\AimSyncBeta\`.
