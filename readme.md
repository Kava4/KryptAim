<div align="center">

  <img
    src="https://raw.githubusercontent.com/Kava4/AimSync/main/Server/static/AimSync_logo.png"
    alt="AimSync Logo"
    width="160"
    height="160"
  />

  # AimSync
  ### High-Integrity Hardware Input Framework

  [![GitHub stars](https://img.shields.io/github/stars/Kava4/AimSync?style=for-the-badge&color=00CFFF)](https://github.com/Kava4/AimSync/stargazers)
  [![License](https://img.shields.io/github/license/Kava4/AimSync?style=for-the-badge)](LICENSE.md)
  [![Support on Ko-fi](https://img.shields.io/badge/Support-Ko--fi-F16061?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/kava4)
  [![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/kava4)

  **AimSync** is a modern, high-performance utility designed specifically for the **Makcu HID hardware**. It provides a seamless web interface to create, visualize, and manage recoil compensation patterns for CS2 and other shooters.
</div>

---

## 🚀 Key Features

*   **Makcu Hardware Integration:** Native support for Makcu HID devices, ensuring low-latency, driver-level mouse movement simulation.
*   **Interactive Pattern Visualizer:** A world-class real-time editor that lets you draw, drag, and simulate recoil paths with ease.
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
| User guide | [Overview](docs/user-guide/overview.md), [Game Engine](docs/user-guide/game-engine.md), [Free trial](docs/user-guide/licensing.md) |
| Reference | [Configuration](docs/reference/configuration.md), [Local API](docs/reference/local-api.md), [Cloud API](docs/reference/cloud-api.md) |
| Development | [Setup](docs/development/setup.md), [Architecture](docs/development/architecture.md), [Cloud deploy](docs/development/cloud-deployment.md) |
| Support | [Troubleshooting](docs/support/troubleshooting.md), [FAQ](docs/support/faq.md) |

---

## Roadmap

See [docs/project/roadmap.md](docs/project/roadmap.md) (also [dev_roadmap.md](dev_roadmap.md) in the repo root).

---

## ⚖️ Disclaimer

*This software is intended for educational and hardware testing purposes. Use of automation tools in online multiplayer games may violate terms of service. Use responsibly.*


<!--
