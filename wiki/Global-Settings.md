# Global settings

Controls that apply across recoil and shared app options.

---

## Master switch

- **Recoil enabled** — global on/off for compensation.
- Toggle hotkey (default **M4**).

---

## Input method

- **Hardware (Makcu)** — production / dual-PC.
- **Win32 (dev)** — local mouse only, for `run_dev.bat`.

---

## Randomisation

Optional X/Y jitter and control sliders for spray variation.

---

## AI Runtime (slim exe)

One-time install of embeddable Python + AI stack to:

```
%APPDATA%\KryptAim\runtime\
```

Checklist shows: embed Python · virtualenv · AI packages.

Required before the AI engine can run (lite build only).

---

## Updates

- **Check for updates** — compares with [GitHub Releases](https://github.com/Kava4/KryptAim/releases).
- **Install update** — downloads new `KryptAim.exe` and restarts (built exe only).

Version source: `release/version.json` in the repo.

---

## License & AI access

**Default:** AI is free — badge shows **Free · AI unlocked**.

When `release/app-config.json` sets `ai_premium_only: true`, this section shows supporter key validation (Ko-fi).

Dev key: `DEV-KRYPTAIM` with `scripts\run_dev.bat`.

---

## Shutdown

**Shutdown PC on Stop** — Windows shutdown when closing KryptAim.

---

## Related

- [Configuration](Configuration)
- [Slim exe distribution](Slim-Exe-Distribution)
- [Cloud API](Cloud-API) — remote flags
