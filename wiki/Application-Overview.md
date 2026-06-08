# Application overview

AimSync starts a local Flask server and opens a tabbed web dashboard.

---

## Tabs

| Tab | Purpose |
|-----|---------|
| **Global Settings** | Master switch, hotkeys, input method, Makcu status |
| **Safety Features** | Randomization, global X/Y multipliers |
| **Simple Recoil** | Quick vertical/horizontal sliders |
| **Recoil Lab** | Advanced pattern editor + visualizer |
| **Game Engine** | Per-game weapon profiles (CS2) |
| **AI** | Detection, aim assist, triggerbot, NDI capture |

---

## Input methods

| Method | Description |
|--------|-------------|
| **Hardware (Makcu)** | Recommended — low-latency HID movement |
| **Software** | Legacy / testing without Makcu |

---

## Startup behavior

1. `main.py` acquires single-instance mutex.
2. Flask serves UI on port **5000** (all interfaces).
3. Makcu connection attempted in background.
4. AI engine loads when enabled in config.
5. Hotkey monitor runs for recoil + AI binds.

---

## Data locations

| Data | Dev (source) | Installed / exe |
|------|--------------|-----------------|
| Config | `.aimsync-data/config.json` | `%APPDATA%\AimSync\config.json` |
| Saved patterns | `.aimsync-data/saved_patterns/` | `%APPDATA%\AimSync\saved_patterns\` |
| AI models | `.aimsync-data/bin/models/` | `%APPDATA%\AimSync\bin\models\` |
| AI configs | `.aimsync-data/bin/configs/` | `%APPDATA%\AimSync\bin\configs\` |
| Debug log | — | `%APPDATA%\AimSync\aimsyc_debug.log` |

Legacy `.beta-data/` and `%APPDATA%\AimSyncBeta\` still work if present.
