# AimSync Beta: AI / Trigger Engine

Beta-only integration of an Aimmy-compatible AI pipeline inside AimSync, using a **single Makcu connection** shared with recoil.

## What is included

- ONNX YOLOv8 detection (`.onnx` models from Aimmy)
- Aimmy-style `.cfg` settings (FOV, trigger delay, confidence, toggles)
- Auto Trigger and basic aim assist through Makcu
- Model upload and download from the Aimmy community GitHub store
- Optional phase-2 features when `ai_phase` is `2`: sticky aim tuning, prediction smoothing

## What is not included (yet)

- ESP / FOV overlay windows
- Aimmy anti-recoil (use AimSync recoil instead)
- Full movement-path parity (Bezier, Perlin, etc.) — planned for phase 2

## Stable channel

The normal **AimSync** build does not start the AI thread, does not register active ONNX sessions, and does not show the AI Engine UI. Settings keys `ai_*` are not merged into stable `config.json`.

## Requirements

```bash
pip install -r requirements.txt -r requirements-beta.txt
```

Run beta:

```bash
set AIMSYNC_CHANNEL=beta
python main.py
```

Or use `run_beta.bat` if present in your tree.

## Usage

1. Close **Aimmy** (only one app may open Makcu).
2. Copy `.onnx` models into `.beta-data/bin/models/` (dev) or import via the UI.
3. Open the **AI Engine** tab, upload or download a model, select a `.cfg`.
4. Enable **Engine enabled**, **Auto Trigger** / **Aim Assist**, set aim keybinds.
5. Hold your aim keybind in-game while the engine is enabled.

## Troubleshooting

| Issue | Action |
|-------|--------|
| Makcu in use | Close Aimmy and other tools using the device |
| Model not loading | Install `requirements-beta.txt`; confirm `.onnx` is YOLOv8 compatible |
| No detections | Lower **AI Minimum Confidence**; increase **FOV Size** |
| AI tab missing | Run **AimSync Beta**, not stable |

See [aimmy-pipeline-map.md](aimmy-pipeline-map.md) for implementation mapping.
