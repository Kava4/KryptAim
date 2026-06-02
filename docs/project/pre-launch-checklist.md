# Early Access pre-launch checklist

Track progress for the first public Early Access release. Work through items in order.

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | [Fresh release build + smoke test](#1-fresh-release-build--smoke-test) | Done | Single `dist\AimSync.exe`; smoke test passed |
| 2 | [Trial end-to-end](#2-trial-end-to-end) | Pending | |
| 3 | [Early Access messaging](#3-early-access-messaging) | Pending | |
| 4 | [GitHub Release + changelog](#4-github-release--changelog) | Pending | |
| 5 | [README / landing links](#5-readme--landing-links) | Pending | |
| 6 | [Ko-fi license flow](#6-ko-fi-license-flow) | Pending | |

---

## 1. Fresh release build + smoke test

### 1a. Rebuild the Windows package

From project root (full source tree required):

```powershell
.\venv\Scripts\activate
python build_app.py
```

Output: **`dist\AimSync.exe`** only (one-file build; no `_internal` folder to distribute).

### 1b. Confirm build includes recent fixes

After build, you can unpack or run once and verify the dashboard shows:

- `hx-trigger="load, every 15s"` on `#license-status`
- `const startTab = 'global'`
- `formatTrialLabel` in the countdown script

### 1c. Smoke test (clean machine or VM recommended)

Automated check on dev PC (2026-06-02): exe starts, `HTTP 200`, page contains **Global Settings** and **Start Free Trial**.

| Step | Pass? |
|------|-------|
| Copy only `AimSync.exe` to test PC (no venv, no extra folders) | ☑ |
| Double-click `AimSync.exe` | ☑ |
| Browser opens dashboard | ☑ |
| Default tab is **Global Settings** | ☑ |
| **Start Free Trial** → countdown appears | ☑ |
| **Game Engine** tab is unlocked | ☑ |
| Master switch toggles without error | ☑ |
| Quit from UI exits cleanly | ☑ |

### 1d. Firewall note

Windows may prompt for port **5000** on first run — allow on private networks for LAN access.

---

## 2. Trial end-to-end

*(Filled in when we reach checklist item 2.)*

---

## 3. Early Access messaging

*(Pending.)*

---

## 4. GitHub Release + changelog

*(Pending.)*

---

## 5. README / landing links

*(Pending.)*

---

## 6. Ko-fi license flow

*(Pending.)*
