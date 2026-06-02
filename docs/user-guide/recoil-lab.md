# Recoil Lab

Recoil Lab (Advanced Recoil) is the pattern authoring environment. You draw or import a spray path, preview it on the canvas visualizer, and save named patterns locally or share them to the cloud (premium).

## Pattern format

Each step is a movement segment stored as JSON:

```json
[
  { "x": 0, "y": -4, "d": 50 },
  { "x": -1, "y": -3, "d": 45 }
]
```

| Field | Meaning |
|-------|---------|
| `x` | Horizontal pixels (or units) |
| `y` | Vertical pixels |
| `d` | Delay before this step (ms) |

## Visualizer

- Drag points to edit the path
- Context menu for insert/delete steps
- **CS Fix (x20)** — bulk scale for view-angle style values
- Live preview while editing

## Save and load

| Action | Description |
|--------|-------------|
| Save | Writes `saved_patterns/<name>.json` under the config directory |
| Load | Restores a named pattern into the editor |
| Delete | Removes a saved file |

## Loop mode

When **loop** is enabled, the pattern repeats from the first step after the last step completes.

## Cloud repository (premium)

| Action | Description |
|--------|-------------|
| Refresh Community | Lists patterns from Cloud API |
| Share | Uploads current pattern (requires donator or trial) |
| Import | Loads community pattern into editor |

Set **cloud username** before sharing so patterns are attributed correctly.

## Related API

- `POST /api/recoil/advanced_pattern`
- `POST /api/recoil/loop`
- `POST /api/recoil/pattern/save`
- `POST /api/recoil/pattern/load`
- `POST /api/recoil/pattern/delete`
- `GET /api/recoil/cloud/list`
- `POST /api/recoil/cloud/upload`
- `GET /api/recoil/cloud/load`

## See also

- [Pattern Generator](../development/pattern-generator.md) — build profiles from GIFs
- [Cloud API](../reference/cloud-api.md)
