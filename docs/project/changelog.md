# Changelog

All notable user-facing changes to AimSync documentation and product behavior. Version numbers follow [GitHub Releases](https://github.com/Kava4/AimSync/releases) when tagged.

## v0.1.0 — Early Access

- Dashboard shows **v0.1.0 · Early Access** in navbar and boot screen
- First public Windows release (`AimSync.exe`)

## Unreleased (documentation & trial)

### Added

- Professional wiki structure under `docs/`
- Free trial: 2 hours active use per calendar day (Cloud API + Supabase)
- Live trial countdown in dashboard
- Default startup tab: Global Settings

### Fixed

- Duplicate Flask license routes blocking trial activation
- Premium cache sync after trial / license validation
- Supabase schema migration for `display_name` and trial columns
- Game Engine unlock after successful trial

### Documentation

- Split user guide, reference, development, and support sections
- Accurate local and cloud API references
- Cloud deployment and trial setup guide

---

## How to report changes

When cutting a release, add a dated section above with:

- **Added** — new features
- **Changed** — behavior changes
- **Fixed** — bug fixes
- **Security** — vulnerability patches

Link issues and PRs where applicable.
