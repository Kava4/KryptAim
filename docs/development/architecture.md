# Architecture

## System context

```
┌──────────────┐     HTTP      ┌─────────────────┐
│   Browser    │◄────────────►│  Flask (5000)   │
│  Dashboard   │              │  Server/app.py  │
└──────────────┘              └────────┬────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
            ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
            │ config_manager│  │ cloud_manager │  │ recoil_routes│
            └──────────────┘  └───────┬──────┘  └──────────────┘
                                       │ HTTPS
                                       ▼
                              ┌─────────────────┐
                              │ Vercel Cloud API │
                              └─────────────────┘

┌──────────────┐
│   main.py    │
│  Tkinter +   │
│  threads     │
└──────┬───────┘
       │
       ├── run_flask()      (daemon)
       ├── run_recoil_loop() (daemon)
       └── monitor_hotkeys() (daemon)
              │
              ▼
       ┌──────────────┐     ┌──────────────────┐
       │ recoil.py    │────►│ makcu_manager /   │
       │ (engine)     │     │ software_manager │
       └──────────────┘     └──────────────────┘
```

## Module responsibilities

| Module | Role |
|--------|------|
| `main.py` | Process lifecycle, browser launch, thread spawning |
| `Server/app.py` | Routes, license proxy, game list, template render |
| `Server/routes/recoil_routes.py` | HTMX form handlers for recoil settings |
| `Server/cloud_manager.py` | Cloud HTTP client, premium RAM cache |
| `Config/config_manager.py` | JSON load/save, pattern files |
| `Recoil/recoil.py` | Main compensation loop |
| `Recoil/weapon_data.py` | Game/weapon registry |
| `Makcu/makcu_manager.py` | HID connect, move, button state |
| `Makcu/software_manager.py` | SendInput fallback |
| `Cloud/api/index.py` | License, patterns, webhooks |

## Recoil execution flow

1. Hotkey or UI enables `recoil_enabled`.
2. Loop reads `recoil_mode` and loads pattern or game profile.
3. While fire conditions match (LMB / RMB rules), compute next `(x, y)` step.
4. Apply safety scaling and randomization.
5. Submit movement via hardware or software manager.
6. Sleep for step delay; repeat.

## License flow

1. UI POSTs to local `/api/recoil/validate_license`.
2. Local server POSTs JSON to Cloud `/api/license/validate` with `hwid`.
3. Cloud reads/writes Supabase `licenses` row (`TRIAL_*` or email key).
4. Response updates `sync_premium_cache()` and `config.is_premium`.
5. `HX-Refresh` reloads page when premium newly granted.

## Configuration persistence

- Runtime: in-memory `load_config()` dict
- Disk: atomic write via `save_config()`
- Frozen builds: `%APPDATA%\AimSync\`

## Design principles

- **Hardware first** — software mode is explicit opt-in.
- **Server-side license** — premium not enforced by config alone.
- **HTMX-first UI** — small partial updates without SPA framework.
- **Separation** — Cloud API deployable independently of desktop builds.

## See also

- [Local API](../reference/local-api.md)
- [Licensing](../user-guide/licensing.md)
