# Application overview

AimSync starts a local Flask server and opens a tabbed web dashboard.

---

## Tabs

| Tab | Purpose |
|-----|---------|
| **Global Settings** | Recoil master switch, input method, license (when premium), **AI runtime install**, **updates** |
| **Game Engine** | CS2 weapon spray profiles (CT/T sides, rifles & SMGs) |
| **AimSync AI** | NDI capture, YOLO model, CT/T target class, aim assist & triggerbot |

---

## Input methods

| Method | Description |
|--------|-------------|
| **Hardware (Makcu)** | Recommended — low-latency HID movement on the gaming PC via Makcu |
| **Win32 (dev)** | Local mouse only — for development without Makcu |

---

## Startup behavior

1. `main.py` acquires single-instance mutex.
2. Flask serves UI on port **5000** (all interfaces).
3. Makcu connection attempted in background.
4. AI worker starts when runtime is installed **and** access is allowed (free by default).
5. Update check runs on dashboard load (GitHub Releases).

---

## Data locations

| Data | Path |
|------|------|
| Config | `%APPDATA%\AimSync\config.json` |
| AI models | `%APPDATA%\AimSync\models\` |
| AI runtime (slim exe) | `%APPDATA%\AimSync\runtime\` |
| Update downloads | `%APPDATA%\AimSync\updates\` |
| App log | `%APPDATA%\AimSync\aimsync.log` |

**Slim exe:** Recoil works immediately. Install AI from **Global Settings → AI Runtime**.

---

## AI access

**Default:** AI is **free** for everyone.

To require supporter keys later, set `ai_premium_only: true` in [release/app-config.json](https://github.com/AimSyncCore/AimSync/blob/Beta/release/app-config.json) on GitHub (no rebuild needed).

---

## Related

- [Global settings](Global-Settings)
- [AI Engine](AI-Engine)
- [Slim exe distribution](Slim-Exe-Distribution)
