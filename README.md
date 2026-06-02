<p align="center">
  <img src="https://i.ibb.co/LhHngKZF/Aim-Sync-logo.png" alt="AimSync Logo" width="160" height="160" />
</p>

<h1 align="center">AimSync</h1>
<h3 align="center">High-Integrity Hardware Input Framework</h3>

<p align="center">
  <a href="https://ko-fi.com/kava4"><img src="https://img.shields.io/badge/Support-Ko--fi-F16061?style=for-the-badge&amp;logo=ko-fi&amp;logoColor=white" alt="Support on Ko-fi" /></a>
  <a href="https://paypal.me/kava4"><img src="https://img.shields.io/badge/Donate-PayPal-00457C?style=for-the-badge&amp;logo=paypal&amp;logoColor=white" alt="Donate via PayPal" /></a>
</p>

<p align="center">
  <strong>AimSync</strong> is a modern, high-performance utility designed specifically for the <strong>Makcu HID hardware</strong>. It provides a seamless web interface to create, visualize, and manage recoil compensation patterns for CS2 and other shooters.
</p>

---

## 🚀 Key Features

*   **Makcu Hardware Integration:** Native support for Makcu HID devices, ensuring low-latency, driver-level mouse movement simulation.
*   **Interactive Pattern Visualizer:** A world-class real-time editor that lets you draw, drag, and simulate recoil paths with ease.
*   **Pattern Generator (Image/GIF -> Weapon Data):** Turn spray captures into canonical `weapon_data.py` entries with manual correction, frame slider, and direct append.
*   **Safety-First Design:** Integrated safety modifiers including randomization strength and global movement scaling to ensure patterns feel natural.
*   **Game-Specific Intelligence:** Dedicated CS2 engine that scales weapon-specific patterns based on your in-game sensitivity.
*   **Modern Tabbed UI:** A sleek, dark-themed dashboard built with **Tailwind CSS** and **HTMX** for a reactive, single-page application feel.
*   **Global Controls:** Master toggle and customizable keybinds (M4/M5) that work across all recoil modes.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.x, Flask (Lightweight API Server)
- **Frontend:** Tailwind CSS, HTMX, Vanilla JavaScript
- **Hardware Interface:** Custom Makcu HID management
- **Visuals:** HTML5 Canvas (Custom Pattern Engine)

---

## 🎮 UI Overview

| Tab | Description |
| :--- | :--- |
| **Global Settings** | Manage the master switch, keybinds (M4/M5), and activation requirements. |
| **Safety Features** | Fine-tune randomization and global X/Y control multipliers. |
| **Simple Recoil** | Quick sliders for basic vertical and horizontal compensation. |
| **Advanced Recoil** | The core editor. Create complex, multi-step patterns with the visualiser. |
| **CS2 Recoil** | Select weapon profiles (AK-47, M4A1-S) scaled to your sensitivity. |

---

## Pattern Generator Tutorial

This is now a core workflow and a major AimSync selling point.

### Open it

1. Launch AimSync.
2. Go to **Recoil Lab**.
3. Click **Pattern Generator** (opens in a new tab).

### Generate from image or GIF

1. Load media:
   - local file (`.png`, `.jpg`, `.webp`, `.gif`) or
   - direct URL (`https://...`).
2. Use **Auto-Suggest** for initial bullet points.
3. Correct order/positions manually:
   - click to add points
   - right-click canvas to undo last point
   - reorder/delete from the points list.
4. Use **Frame slider** for GIFs to inspect every frame.

### Export and append to Game Engine

1. Keep `Export Mode = Canonical 1:1` for `weapon_data.py` style output.
2. Set Delay (default `100ms` -> `0.1s`).
3. Choose game and weapon name.
4. Click **Generate Pattern** to preview.
5. Click **Append to Game Data** to write into `Recoil/games/<game>.py` (with automatic `.bak` backup).

For detailed docs, see [Pattern Generator guide](docs/user-guide/pattern-generator.md).

---

## 🤝 Support & Contribution

AimSync is an open-source project. If you find it useful, consider supporting development:

- **Cloud Upload:** Share your patterns with the community.
- **CS2 Engine:** Unlock pre-made weapon profiles.
- **Humanization:** Support the development of Bézier curve movement algorithms.

[Become a Supporter on Ko-fi](https://ko-fi.com/kava4)

---

## Documentation

Full wiki-style documentation lives in **[docs/README.md](docs/README.md)**:

| Section | Topics |
|---------|--------|
| Getting started | [Installation](docs/getting-started/installation.md) (use **Releases**—public Git is incomplete), [Quick start](docs/getting-started/quick-start.md) |
| User guide | [Overview](docs/user-guide/overview.md), [Game Engine](docs/user-guide/game-engine.md), [Pattern Generator](docs/user-guide/pattern-generator.md), [Access mode](docs/user-guide/licensing.md) |
| Reference | [Configuration](docs/reference/configuration.md), [Local API](docs/reference/local-api.md), [Cloud API](docs/reference/cloud-api.md) |
| Development | [Setup](docs/development/setup.md), [Architecture](docs/development/architecture.md), [Cloud deploy](docs/development/cloud-deployment.md) |
| Support | [Troubleshooting](docs/support/troubleshooting.md), [FAQ](docs/support/faq.md) |

---

## Roadmap

See [docs/project/roadmap.md](docs/project/roadmap.md) (also [dev_roadmap.md](dev_roadmap.md) in the repo root).

---

## ⚖️ Disclaimer

*This software is intended for educational and hardware testing purposes. Use of automation tools in online multiplayer games may violate terms of service. Use responsibly.*
