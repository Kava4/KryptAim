# CS2 recoil weapons

Spray / automatic weapons that benefit from recoil compensation.  
Excluded: bolt snipers, pump/break shotguns, Zeus, knives, grenades.

## Rifles

| Weapon | ID | Recoil | Steps | Profile |
|--------|-----|--------|-------|---------|
| AK-47 | `assault_rifle` | yes | 29 | smooth (100ms) |
| M4A4 | `m4a4` | yes | 87 | spray (30ms) |
| M4A1-S | `m4a1s` | yes | 18 | smooth |
| FAMAS | `famas` | yes | 71 | spray |
| Galil AR | `galil` | yes | 560 | timed; tail X ×0.82 last 20% |

## SMGs

| Weapon | ID | Recoil | Steps | Profile |
|--------|-----|--------|-------|---------|
| MP9 | `mp9` | yes | 63 | spray |
| MAC-10 | `mac10` | yes | 72 | spray |
| MP7 | `mp7` | yes | 324 | timed; tail X ×0.82 / Y ×0.92 last 25% |
| MP5-SD | `mp5sd` | yes | 360 | timed |
| P90 | `p90` | yes | 600 | timed |
| UMP-45 | `ump45` | yes | 300 | timed |
| PP-Bizon | `bizon` | yes | 768 | timed |


## Pistols (optional / later)

Semi-auto; only worth adding if we support fast spam patterns.

| Weapon | ID | Recoil |
|--------|-----|--------|
| Glock-18 | `glock` | no |
| USP-S | `usps` | no |
| P2000 | `p2000` | no |
| P250 | `p250` | no |
| Five-SeveN | `fiveseven` | no |
| Tec-9 | `tec9` | no |
| CZ75-Auto | `cz75` | no |
| Desert Eagle | `deagle` | no |
| Dual Berettas | `dualies` | no |

## Summary

- **In app:** 12 spray weapons (5 rifles + 7 SMGs)
- **Out of scope:** LMGs, auto-snipers, pistols
- **Sensitivity:** in-game sens only; patterns stored at baseline 1.25, scaled at runtime

### `timed` profile (Galil + aie1123 SMGs)

Matches source script order: **move first**, then sleep until cumulative step deadline.

Tail tune via `WeaponData.TAIL_TUNE`:
- **Galil:** last 20% — X ×0.82
- **MP7:** last 25% — X ×0.82, Y ×0.92
- Other timed SMGs: raw pattern (hardware verified)

Re-bake: `python scripts/bake_aie_weapon.py all-smgs`
