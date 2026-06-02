# Application overview

## What AimSync does

AimSync runs a local web dashboard that configures a background **recoil engine**. While enabled, the engine applies mouse movements through either:

- **Makcu hardware** (preferred), or  
- **Software SendInput** (fallback).

Configuration persists to `config.json`. License state is verified against the Cloud API when premium features are used.

## Main window layout

```
┌──────────────────────────────────────────────────────────┐
│  Sidebar / mobile drawer          │  Main content area   │
│  • Global Settings (default)      │  Active tab panels   │
│  • Safety Features              │                      │
│  • Simple Recoil                │                      │
│  • Recoil Lab                   │                      │
│  • Game Engine (premium/trial)  │                      │
└──────────────────────────────────────────────────────────┘
```

On every launch, the UI opens **Global Settings** first. Your last selected recoil mode (`simple`, `advanced`, or `CS2`) is remembered for when you switch tabs.

## Technology stack

| Layer | Technology |
|-------|------------|
| Desktop host | Python, Tkinter (tray lifecycle) |
| Web server | Flask on port 5000 |
| UI | HTML templates, Tailwind CSS, HTMX |
| Pattern UI | Canvas visualizer (JavaScript) |
| Hardware | `makcu` Python package |
| Cloud | Vercel serverless + Supabase |

## Background processes

| Thread | Role |
|--------|------|
| Flask server | Serves dashboard and REST API |
| Recoil loop | Applies compensation while enabled |
| Hotkey monitor | Weapon cycle keybind (Game Engine) |
| License poll | Refreshes trial countdown (~15s) |

## Premium gating

These require a valid donator key or active daily trial:

- **Game Engine** tab and weapon routes
- **Share** to cloud repository (Recoil Lab)
- Some integrity checks in the hardware status panel

Free tier includes Global Settings, Safety Features, Simple Recoil, and Recoil Lab (local patterns only).

## Stopping the application

Use **Stop Application** in the sidebar. Optionally enable **Shutdown PC on exit** in Global Settings.

## See also

- [Global settings](global-settings.md)
- [Licensing and free trial](licensing.md)
- [Architecture](../development/architecture.md)
