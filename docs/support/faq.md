# FAQ

## General

**What is AimSync?**  
A desktop utility with a local web UI for configuring recoil compensation through Makcu hardware or software mouse simulation.

**Does it work without Makcu?**  
Yes, in software (SendInput) mode, but hardware mode is recommended.

**Which games are supported?**  
CS2, Valorant, PUBG, R6S, and Rust have active Game Engine modules. More titles are listed in the UI with varying completeness.

**Can I build AimSync from the GitHub source?**  
No—not from the public repository alone. Core engine, Makcu integration, API routes, and build scripts are withheld to protect the project. Download a [release build](https://github.com/Kava4/AimSync/releases/latest) instead. Details: [Installation](../getting-started/installation.md).

**Why is the repo public if I cannot run it?**  
The open repo includes the dashboard, documentation, game profile data, Pattern Generator, and community discussion—not the full proprietary engine.

---

## Licensing

**What does the free trial include?**  
The same premium features as donators (Game Engine, cloud upload) for 2 hours of active use per day.

**Does the trial require a credit card?**  
No. Click **Start Free Trial**; activation uses your machine HWID.

**Can I use one trial on multiple PCs?**  
Each machine has its own `TRIAL_<hwid>` record.

**How do I get a permanent license?**  
Support via [Ko-fi](https://ko-fi.com/kava4) or PayPal; keys are tied to your email.

---

## Usage

**Why does the app open Global Settings first?**  
That is the intentional default startup tab.

**Where is my config saved?**  
Dev: project folder. Installed: `%APPDATA%\AimSync\config.json`.

**Can I edit config.json while running?**  
Possible, but UI may overwrite values. Restart after manual edits. `is_premium` is revalidated from the cloud.

---

## Technical

**Is there a public REST API on my PC?**  
Yes, Flask on port 5000 on your LAN. See [Local API](../reference/local-api.md).

**Why tier `Donator` during trial?**  
The API uses one premium flag for all paid/trial access; the UI shows trial time separately.

---

## Legal

**Can I use this in matchmaking?**  
Many games prohibit automation. You are responsible for compliance with publisher terms.

See [README legal notice](../../README.md).
