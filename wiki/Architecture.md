# Architecture

High-level module map for the **rebuild** tree (2026).

---

## Process model

```
main.py
  └── app/web/runner.py
        ├── Flask (web/app.py)       → browser UI + REST API
        ├── Recoil worker thread     → CS2 spray via Makcu
        └── AI worker thread         → NDI + YOLO + aim/trigger (when runtime ready)
```

Single-instance mutex: `AimSync_Rebuild_v1`

---

## Layout

```
AimSync/
├── main.py
├── app/
│   ├── core/          # config, cloud, licensing, updates, feature flags
│   ├── makcu/         # HID manager
│   ├── recoil/        # CS2 recoil engine + weapon data
│   ├── ai/            # capture, inference, engine, model catalog
│   ├── bootstrap/     # slim-exe AI runtime install (embed Python + venv)
│   └── web/           # runner (Flask + workers)
├── web/
│   ├── app.py         # Flask routes
│   ├── routes/        # recoil, ai, bootstrap, updates, access
│   ├── templates/     # index.html, _ai_panel.html
│   └── static/        # CSS, logos, hotkey JS
├── scripts/           # run, build, install
├── tests/
├── wiki/              # synced to GitHub Wiki on push
├── website/           # React marketing site (GitHub Pages)
└── release/           # version.json, app-config.json (remote flags)
```

Legacy monolith is **not** in the repo (local `.backup-legacy/` only).

---

## Recoil path

```
config.json → app/recoil/engine.py → Makcu move(dx, dy)
```

CS2 weapon profiles in `app/recoil/` + `%APPDATA%\AimSync\config.json`.

---

## AI path

```
NDI frame → YOLO (Ultralytics) → CT/T class filter → aim/trigger → Makcu
```

Key modules:
- `app/ai/capture*.py` — NDI capture
- `app/ai/inference.py` — Ultralytics / ONNX
- `app/ai/targets.py` — class filter + aim point
- `app/ai/engine.py` — main loop
- `app/ai/model_sources.py` — GitHub + Aimmy model catalog

Slim exe: AI packages live in `%APPDATA%\AimSync\runtime\` after bootstrap.

---

## Config

`app/core/config.py` — `DEFAULTS` merged into `%APPDATA%\AimSync\config.json`.

---

## UI

- **Tailwind CSS** + **HTMX** + vanilla JS
- Tabs: Global Settings · Game Engine (CS2) · AimSync AI
- Templates: `web/templates/`

---

## Remote flags & updates

- `release/app-config.json` on GitHub — e.g. `ai_premium_only` (default `false`)
- GitHub Releases — in-app update check (`app/core/updates.py`)
