# Recoil Lab

Advanced pattern editor with real-time visualizer.

---

## Features

- Draw and drag recoil points on canvas
- Multi-step patterns with per-step delay
- Save / load named patterns locally
- Share patterns to cloud (community list)
- Open **Pattern Generator** in new tab

---

## Workflow

1. Build or load a pattern in the visualizer.
2. Tune loop / step timing.
3. **Save pattern** with a name.
4. **Load pattern** to switch profiles.
5. Hold global hotkey in-game to run the active pattern.

---

## Cloud share

- Set cloud username in settings.
- **Share** uploads pattern JSON to the hosted API.
- **Refresh Community** loads shared patterns (may be empty until users upload).

See [Cloud API](Cloud-API).

---

## Related

- [Pattern Generator](Pattern-Generator)
- [Local API](Local-API) — `/api/recoil/save_pattern`, `load_pattern`
