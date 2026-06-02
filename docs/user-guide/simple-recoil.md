# Simple recoil

Simple Recoil applies a fixed horizontal and vertical pull on each shot interval. It is the fastest mode to tune when you only need basic downward compensation.

## Controls

| Setting | Description |
|---------|-------------|
| X | Horizontal movement per tick (negative = left, positive = right) |
| Y | Vertical movement per tick (typically negative to pull down) |
| Delay | Milliseconds between application steps while firing |

Changes save automatically via HTMX to the local API.

## When to use Simple Recoil

- Single-fire or low-rate weapons with predictable kick
- Quick testing before building a full pattern in Recoil Lab
- Games without a dedicated Game Engine profile yet

## Interaction with safety features

Global X/Y control and randomization from [Safety features](safety-features.md) multiply and jitter Simple Recoil output.

## Related API

- `POST /api/recoil/x`
- `POST /api/recoil/y`
- `POST /api/recoil/delay`
- `POST /api/recoil/mode` — set mode to `simple`

## See also

- [Recoil Lab](recoil-lab.md) — multi-step patterns
- [Game Engine](game-engine.md) — weapon-specific sprays
