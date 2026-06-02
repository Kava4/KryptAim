# AimSync Documentation

Welcome to the AimSync knowledge base. This wiki covers installation, daily use, configuration, APIs, development, and operations.

**AimSync** is a desktop utility for Makcu HID hardware that provides a local web dashboard to configure recoil compensation, visualize patterns, and sync optional cloud features.

---

## Documentation map

### Getting started

| Page | Description |
|------|-------------|
| [Installation](getting-started/installation.md) | **Releases (recommended)** vs public GitHub clone (incomplete by design) |
| [Quick start](getting-started/quick-start.md) | Five-minute setup: hardware, access mode, first profile |

### User guide

| Page | Description |
|------|-------------|
| [Application overview](user-guide/overview.md) | UI layout, tabs, input methods, startup behavior |
| [Global settings](user-guide/global-settings.md) | Master switch, hotkeys, input method, shutdown |
| [Safety features](user-guide/safety-features.md) | Randomization and global X/Y scaling |
| [Simple recoil](user-guide/simple-recoil.md) | Slider-based compensation |
| [Recoil Lab](user-guide/recoil-lab.md) | Pattern editor, visualizer, save/load, cloud share |
| [Game Engine](user-guide/game-engine.md) | Per-game weapon profiles and sensitivity |
| [Access mode](user-guide/licensing.md) | Current free mode and future licensing placeholder |
| [Pattern Generator](user-guide/pattern-generator.md) | Build weapon patterns from image/GIF spray captures |

### Reference

| Page | Description |
|------|-------------|
| [Configuration](reference/configuration.md) | `config.json` schema and file locations |
| [Local API](reference/local-api.md) | Flask endpoints on port 5000 |
| [Cloud API](reference/cloud-api.md) | Vercel license and pattern services |
| [Weapons and games](reference/weapons-and-games.md) | Supported titles and profile model |

### Development

| Page | Description |
|------|-------------|
| [Developer setup](development/setup.md) | Clone, dependencies, run, test, build |
| [Architecture](development/architecture.md) | Modules, data flow, threading |
| [Pattern Generator](development/pattern-generator.md) | Standalone GIF/image analysis tool |
| [Cloud deployment](development/cloud-deployment.md) | Vercel + Supabase deployment notes |

### Support

| Page | Description |
|------|-------------|
| [Troubleshooting](support/troubleshooting.md) | Common errors and fixes |
| [FAQ](support/faq.md) | Frequently asked questions |

### Project

| Page | Description |
|------|-------------|
| [Roadmap](project/roadmap.md) | Planned features and status |
| [Changelog](project/changelog.md) | Release history |

---

## Quick links

- [Project README](../README.md) — feature summary and badges
- [GitHub repository](https://github.com/Kava4/AimSync)
- [Ko-fi support](https://ko-fi.com/kava4)
- [Latest release](https://github.com/Kava4/AimSync/releases/latest)

---

## Conventions in this wiki

- **Local API** — HTTP server started by `main.py` (default `http://<LAN-IP>:5000`).
- **Cloud API** — Hosted at `https://project-mkgdr.vercel.app` (community patterns and cloud services).
- **Access mode** — Currently free for all users; licensing hooks are placeholders.

---

## Legal and responsible use

AimSync is intended for educational use and hardware testing. Using input automation in online games may violate publisher terms of service. You are responsible for how you use this software.

See [LICENSE](../LICENSE) for license terms.
