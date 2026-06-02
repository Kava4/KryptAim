# Pattern Generator

Standalone tool under `PatternGenerator/` for building recoil profiles from visual references (GIFs or images). Output is pasted into `Recoil/games/*.py` or used in Recoil Lab.

## Purpose

1. Import a recording of weapon spray (crosshair + impacts).
2. Detect trajectory per frame (OpenCV / custom analyzers).
3. Export compensation vectors.
4. Integrate manually into AimSync weapon data.

## Components

| Path | Role |
|------|------|
| `PatternGenerator/gui.py` | CustomTkinter UI |
| `PatternGenerator/engine/image_analyzer.py` | Frame analysis |
| `PatternGenerator/engine/trajectory_detector.py` | Path detection |
| `PatternGenerator/engine/pattern_calculator.py` | Delta computation |

## Run

```powershell
cd PatternGenerator
python gui.py
```

See `PatternGenerator/readme.md` for build scripts (`build_generator.bat`).

## Workflow

1. Load GIF or image sequence.
2. Calibrate crosshair / impact detection if needed.
3. Review detected points; edit manually in UI.
4. Export Python list or JSON compatible with weapon modules.
5. Copy into the target weapon attribute in `Recoil/games/<game>.py`.
6. Test in Game Engine with matching sensitivity.

## Limitations

- Auto-detection quality depends on source media (contrast, FPS, UI clutter).
- Does not write to `config.json` or cloud automatically.
- CS2 AK-style profiles are the most mature calibration target.

## See also

- [Weapons and games](../reference/weapons-and-games.md)
- [Recoil Lab](../user-guide/recoil-lab.md)
