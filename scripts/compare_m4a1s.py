"""Compare CS2 Pulse M4A1-S GIF detection vs built-in laser pattern."""
from __future__ import annotations

from urllib.request import Request, urlopen

from PatternGenerator.engine import build_recoil_steps, detect_points_and_preview, laser_fit_steps
from Recoil.weapon_data import WeaponData

URL = "https://cs2pulse.com/wp-content/uploads/2024/02/M4A1-S-Spray-Pattern.gif"


def summarize(name: str, steps: list[tuple[float, float, float]]) -> None:
    xs = [s[0] for s in steps]
    ys = [s[1] for s in steps]
    print(f"\n=== {name} ({len(steps)} steps) ===")
    print(f"  sum_x={sum(xs):.1f}  sum_y={sum(ys):.1f}")


def main() -> None:
    data = urlopen(Request(URL, headers={"User-Agent": "AimSync-compare/1.0"}), timeout=20).read()
    detected = detect_points_and_preview(data, "cs2pulse")
    pts = detected["suggested_points"]
    print(f"detected_points={len(pts)}")

    builtin = WeaponData.get_game_data("cs2").m4a1s
    summarize("Built-in laser", builtin)

    fitted = laser_fit_steps(pts, builtin)
    summarize("Laser fit from GIF", fitted)

    print("\n--- Side-by-side ---")
    print("  # |  BUILTIN dx,dy  |  LASER FIT dx,dy")
    for i in range(len(builtin)):
        b = builtin[i]
        g = fitted[i]
        print(f"  {i+1:2d} | ({b[0]:5.1f},{b[1]:5.1f}) | ({g[0]:5.1f},{g[1]:5.1f})")


if __name__ == "__main__":
    main()
