# Architecture

High-level module map.

---

## Process model

```
main.py
  ├── Flask (Server/app.py)     → browser UI + REST API
  ├── Recoil engine thread      → pattern execution
  ├── AI engine thread          → capture + inference + aim
  ├── Hotkey monitor            → global binds
  └── Makcu manager             → HID I/O
```

Single-instance mutex: `AimSync_SingleInstance_v1`

---

## Recoil path

```
config.json → Recoil engine → Makcu move(dx, dy)
```

Modes: simple sliders, advanced pattern array, game weapon profiles.

---

## AI path

```
NDI/MSS frame → YOLO (Ultralytics) → target pick → aim/trigger logic → Makcu
```

Key modules:
- `capture.py` / `capture_ndi.py` — frame source
- `inference_ultralytics.py` — CUDA inference
- `aim.py` + `movement/` — pointer paths
- `trigger.py` — auto-fire zone
- `profiles.py` + `.cfg` — classic aim-style sliders

---

## Config

`Config/config_manager.py` — load/save `config.json`, merge `AI_DEFAULTS`.

App data dir: `Config/app_identity.py` → `%APPDATA%\AimSync`.

---

## UI

- **Tailwind CSS** + **HTMX** + vanilla JS
- Templates: `Server/templates/`
- AI panel partial: `_ai_engine_panel.html`

---

## Threading

AI engine and recoil run on background threads; Flask handles HTTP. Config access uses `RLock`.
