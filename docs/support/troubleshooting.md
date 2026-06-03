# Troubleshooting

## Application will not start

| Symptom | Check |
|---------|--------|
| Port already in use | Close other apps on port 5000 or change Flask port in code |
| `ModuleNotFoundError` after `git clone` | Expected on public GitHub—use [Releases](https://github.com/Kava4/AimSync/releases/latest), not source clone. See [Installation](../getting-started/installation.md) |
| Missing `recoil.py` / `makcu_manager.py` / `Server/routes` | Core files are intentionally not published; install the official `.exe` |
| Import errors on release build | Re-download release; do not mix old config with new binary |

## Browser does not open

Manually visit `http://127.0.0.1:5000` or the LAN IP printed in the console.

## Makcu not detected

| Step | Action |
|------|--------|
| 1 | Connect device before launch |
| 2 | Confirm USB and drivers |
| 3 | Set input method to **Hardware** |
| 4 | Check `/api/recoil/hardware-check` in UI |

Message `Running in management-only mode` means no hardware at startup; reconnect and restart.

## AI Engine (beta only)

| Symptom | Action |
|---------|--------|
| AI tab not visible | Run **AimSync Beta** (`AIMSYNC_CHANNEL=beta` or `AimSyncBeta.exe`) |
| `AI engine is available only in beta` | Same as above — stable build intentionally returns 404 |
| Makcu in use | Close **Aimmy** and any other tool using the device; only AimSync Beta may hold the COM port |
| Model fails to load | `pip install -r requirements-beta.txt`; use Aimmy-compatible YOLOv8 `.onnx` |
| No detections | Lower **AI Minimum Confidence**; verify model matches your game |

See [Beta AI engine](../project/beta-release-ai-engine.md).

## Trial / license issues

| Symptom | Fix |
|---------|-----|
| Trial activation failed | Run `Cloud/supabase_trial_migration.sql`; redeploy Vercel |
| Cloud Error 500 | Read `detail` in response; verify `SUPABASE_KEY` is service role |
| Game Engine locked after trial | Restart AimSync; Ctrl+F5 browser |
| Countdown not moving | Hard refresh; confirm `license-status` has `hx-trigger="load, every 15s"` |

Test cloud directly:

```powershell
python -c "import requests; print(requests.post('https://project-mkgdr.vercel.app/api/license/validate', json={'key':'FREETRIAL','hwid':'test','activate_trial':True}).text)"
```

## Recoil does nothing

| Check | |
|-------|---|
| Master switch on? | |
| Correct mode tab active? | |
| RMB required but not held? | |
| Simple values zero? | |
| Game Engine sensitivity matches game? | |

## Software mode warning

SendInput is easier to detect than hardware injection. Switch to Makcu for production testing.

## Cloud patterns empty

- Internet connectivity
- Supabase `patterns` table populated
- Cloud API URL matches deployment

## Logs

| Build | Log file |
|-------|----------|
| Dev | `aimsyc_debug.log` in project root |
| Exe | Next to executable |

## Getting help

- [GitHub Discussions](https://github.com/Kava4/AimSync/discussions)
- [Ko-fi](https://ko-fi.com/kava4) (priority support for supporters)
- Include HWID, error text, and Vercel log snippet for license bugs
