# Safety features

Safety features humanize output so compensation feels less mechanical. They apply across Simple Recoil, Recoil Lab, and Game Engine unless disabled globally.

## Master toggle

**Safety features enabled** — When off, randomization and global scale multipliers are bypassed for debugging.

API: `POST /api/recoil/safety_features_toggle`

## Randomization

| Control | Range | Effect |
|---------|-------|--------|
| X randomization strength | 0–100 (UI scale) | Horizontal jitter per step |
| Y randomization strength | 0–100 | Vertical jitter per step |

Higher values add variance; zero disables jitter on that axis.

Recommended starting points:

| Scenario | Suggested strength |
|----------|-------------------|
| Testing / calibration | Low (0–20) |
| General play | Medium (30–50) |
| Maximum humanization | Higher (50–70) |

## Global control multipliers

| Control | Default | Effect |
|---------|---------|--------|
| X control | 100% | Scales horizontal compensation |
| Y control | 100% | Scales vertical compensation |
| Speed control | 100% | Adjusts timing between pattern steps |

Use Y control below 100% if compensation feels too strong; above 100% if too weak.

## Reset

The UI provides a control to reset multipliers to defaults in one action.

## Related API

- `POST /api/recoil/randomisation`
- `POST /api/recoil/random_strength`
- `POST /api/recoil/x_control`
- `POST /api/recoil/y_control`
- `POST /api/recoil/speed_control`
