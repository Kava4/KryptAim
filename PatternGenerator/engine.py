from __future__ import annotations

import base64
import datetime as dt
import io
import re
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from PatternGenerator.gui import SprayPoint, normalize_points, validate_points

try:
    from PIL import Image, ImageChops, ImageSequence
except Exception:  # pragma: no cover
    Image = None
    ImageChops = None
    ImageSequence = None


CS2PULSE_PRESETS: Dict[str, Dict[str, str]] = {
    "famas": {
        "label": "FAMAS",
        "media_url": "https://cs2pulse.com/wp-content/uploads/2024/10/Famas.gif",
        "weapon": "famas",
        "reference_weapon": "m4a1s",
        "horizontal_strength": "0.45",
        "delay_ms": "100",
    },
    "ak47": {
        "label": "AK-47",
        "media_url": "https://cs2pulse.com/wp-content/uploads/2024/10/Ak47.gif",
        "weapon": "ak47",
        "reference_weapon": "ak47",
        "delay_ms": "100",
    },
    "m4a1s": {
        "label": "M4A1-S",
        "media_url": "https://cs2pulse.com/wp-content/uploads/2024/02/M4A1-S-Spray-Pattern.gif",
        "weapon": "m4a1s",
        "reference_weapon": "m4a1s",
        "delay_ms": "100",
    },
}


GAME_FILE_MAP: Dict[str, str] = {
    "cs2": "cs2.py",
    "valorant": "valorant.py",
    "pubg": "pubg.py",
    "apex": "apex.py",
    "cod": "cod.py",
    "r6s": "r6s.py",
    "warzone": "warzone.py",
    "delta_force": "delta_force.py",
    "overwatch": "overwatch.py",
    "the_finals": "the_finals.py",
    "battlefield": "battlefield.py",
    "rust": "rust.py",
}


def _require_pillow() -> None:
    if Image is None:
        raise RuntimeError("Pillow is required for image/GIF processing.")


def _to_data_url_png(img: "Image.Image") -> str:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _collect_frames(image_bytes: bytes) -> List["Image.Image"]:
    _require_pillow()
    src = Image.open(io.BytesIO(image_bytes))
    if getattr(src, "is_animated", False):
        return [frame.convert("RGB") for frame in ImageSequence.Iterator(src)]
    return [src.convert("RGB")]


def _auto_suggest_points(frames: Sequence["Image.Image"], max_points: int = 96) -> List[Tuple[int, int]]:
    if not frames:
        return []
    width, height = frames[0].size
    darkness = [[255 for _ in range(width)] for _ in range(height)]

    for frame in frames:
        gray = frame.convert("L")
        pixels = gray.load()
        for y in range(height):
            row = darkness[y]
            for x in range(width):
                v = pixels[x, y]
                if v < row[x]:
                    row[x] = v

    flat = [v for row in darkness for v in row]
    flat.sort()
    threshold_idx = max(0, int(len(flat) * 0.04) - 1)
    threshold = min(150, flat[threshold_idx] if flat else 100)

    mask = [[darkness[y][x] <= threshold for x in range(width)] for y in range(height)]
    visited = [[False for _ in range(width)] for _ in range(height)]

    components: List[Tuple[float, float, int]] = []
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for y0 in range(height):
        for x0 in range(width):
            if visited[y0][x0] or not mask[y0][x0]:
                continue
            stack = [(x0, y0)]
            visited[y0][x0] = True
            sx = sy = count = 0
            while stack:
                x, y = stack.pop()
                sx += x
                sy += y
                count += 1
                for dx, dy in dirs:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx] and mask[ny][nx]:
                        visited[ny][nx] = True
                        stack.append((nx, ny))
            if 3 <= count <= 600:
                components.append((sx / count, sy / count, count))

    components.sort(key=lambda c: (c[1], c[0]))
    return [(int(x), int(y)) for x, y, _ in components[:max_points]]


def _auto_suggest_cs2pulse(frames: Sequence["Image.Image"]) -> List[Tuple[int, int]]:
    """Extract bullet impacts from CS2 Pulse animated spray GIFs (frame diff)."""
    if not frames or ImageChops is None:
        return []

    width, height = frames[0].size
    x0, y0 = int(width * 0.28), int(height * 0.18)
    x1, y1 = int(width * 0.72), int(height * 0.82)
    crop_w, crop_h = x1 - x0, y1 - y0
    if crop_w <= 0 or crop_h <= 0:
        return []

    points: List[Tuple[int, int]] = []
    prev = Image.new("L", (crop_w, crop_h), 0)
    threshold = 25
    min_pixels = 8

    for frame in frames:
        crop = frame.convert("L").crop((x0, y0, x1, y1))
        diff = ImageChops.difference(crop, prev)
        pixels = diff.load()
        coords = [
            (x, y)
            for y in range(crop_h)
            for x in range(crop_w)
            if pixels[x, y] > threshold
        ]
        if len(coords) >= min_pixels:
            sx = sum(c[0] for c in coords) / len(coords)
            sy = sum(c[1] for c in coords) / len(coords)
            points.append((int(sx + x0), int(sy + y0)))
        prev = crop

    return points


def detect_points_and_preview(image_bytes: bytes, detect_style: str = "generic") -> Dict[str, object]:
    frames = _collect_frames(image_bytes)
    style = (detect_style or "generic").strip().lower()
    if style == "cs2pulse":
        points = _auto_suggest_cs2pulse(frames)
        recommended_frame = max(0, len(frames) - 1)
    else:
        points = _auto_suggest_points(frames)
        recommended_frame = 0

    preview = frames[recommended_frame].copy()
    frame_data_urls = [_to_data_url_png(frame) for frame in frames]
    return {
        "width": preview.width,
        "height": preview.height,
        "preview_data_url": _to_data_url_png(preview),
        "frame_data_urls": frame_data_urls,
        "frame_count": len(frame_data_urls),
        "recommended_frame_index": recommended_frame,
        "detect_style": style,
        "suggested_points": [{"x": x, "y": y} for x, y in points],
    }


def _extract_deltas(
    points: Sequence[SprayPoint],
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    invert_x: bool = True,
    invert_y: bool = True,
) -> List[Tuple[float, float]]:
    sign_x = -1.0 if invert_x else 1.0
    sign_y = -1.0 if invert_y else 1.0
    deltas: List[Tuple[float, float]] = []
    for idx in range(1, len(points)):
        prev = points[idx - 1]
        curr = points[idx]
        dx = (curr.x - prev.x) * scale_x * sign_x
        dy = (curr.y - prev.y) * scale_y * sign_y
        deltas.append((dx, dy))
    return deltas


def _interp_cumulative(cum: Sequence[float], pos: float) -> float:
    if not cum:
        return 0.0
    pos = max(0.0, min(len(cum) - 1, pos))
    i0 = int(pos)
    frac = pos - i0
    i1 = min(i0 + 1, len(cum) - 1)
    return cum[i0] * (1.0 - frac) + cum[i1] * frac


def resample_deltas(deltas: Sequence[Tuple[float, float]], target_count: int) -> List[Tuple[float, float]]:
    """Resample a delta sequence to a fixed step count via cumulative interpolation."""
    if target_count <= 0:
        return []
    if not deltas:
        return [(0.0, 0.0)] * target_count
    if len(deltas) == target_count:
        return [(float(dx), float(dy)) for dx, dy in deltas]

    cum_x = [0.0]
    cum_y = [0.0]
    for dx, dy in deltas:
        cum_x.append(cum_x[-1] + dx)
        cum_y.append(cum_y[-1] + dy)

    segment_count = len(deltas)
    resampled: List[Tuple[float, float]] = []
    for i in range(target_count):
        pos0 = (i / target_count) * segment_count
        pos1 = ((i + 1) / target_count) * segment_count
        cx0 = _interp_cumulative(cum_x, pos0)
        cy0 = _interp_cumulative(cum_y, pos0)
        cx1 = _interp_cumulative(cum_x, pos1)
        cy1 = _interp_cumulative(cum_y, pos1)
        resampled.append((cx1 - cx0, cy1 - cy0))
    return resampled


def _fix_total_drift(
    steps: List[Tuple[float, float, float]],
    target_sum_x: float,
    target_sum_y: float,
) -> List[Tuple[float, float, float]]:
    if not steps:
        return steps
    dx_drift = round(target_sum_x - sum(s[0] for s in steps), 3)
    dy_drift = round(target_sum_y - sum(s[1] for s in steps), 3)
    if dx_drift == 0.0 and dy_drift == 0.0:
        return steps
    last_x, last_y, last_d = steps[-1]
    steps[-1] = (round(last_x + dx_drift, 3), round(last_y + dy_drift, 3), last_d)
    return steps


def _trim_outlier_tail(
    steps: List[Tuple[float, float, float]],
    reference: Sequence[Tuple[float, float, float]],
) -> List[Tuple[float, float, float]]:
    if len(steps) < 4:
        return steps
    dys = [abs(step[1]) for step in steps]
    median_dy = sorted(dys)[len(dys) // 2]
    last_x, last_dy, last_delay = steps[-1]
    cap = max(35.0, median_dy * 4.0)
    if abs(last_dy) > cap:
        ref_dx, ref_dy, ref_delay = reference[min(len(reference) - 1, len(steps) - 1)]
        steps[-1] = (last_x if last_x else ref_dx, ref_dy, last_delay or ref_delay)
    return steps


def laser_fit_steps(
    raw_points: Sequence[dict],
    reference_steps: Sequence[Tuple[float, float, float]],
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    invert_x: bool = True,
    invert_y: bool = True,
    vertical_blend: float = 0.2,
    horizontal_strength: float = 1.0,
) -> List[Tuple[float, float, float]]:
    """Map CS2 Pulse spray shape onto a tuned in-game reference (laser) pattern."""
    del vertical_blend  # kept for API compatibility
    h_strength = max(0.0, min(float(horizontal_strength), 2.0))
    points = normalize_points(raw_points)
    validate_points(points)
    reference = [(_f(x), _f(y), _f(d)) for x, y, d in reference_steps]
    if not reference:
        raise ValueError("Reference pattern is empty.")

    raw_deltas = _extract_deltas(points, scale_x=1.0, scale_y=1.0, invert_x=invert_x, invert_y=invert_y)
    raw_resampled = resample_deltas(raw_deltas, len(reference))

    ref_dx = [step[0] for step in reference]
    ref_dy = [step[1] for step in reference]
    ref_delay = [step[2] for step in reference]

    total_raw_y = sum(abs(dy) for _, dy in raw_resampled) or 1e-6
    total_ref_y = sum(ref_dy) or 1e-6

    raw_sum_x = sum(dx for dx, _ in raw_resampled)
    ref_sum_x = sum(ref_dx)
    weak_horizontal = abs(raw_sum_x) < max(1.0, abs(ref_sum_x) * 0.25)

    raw_energy: List[float] = []
    energy_total = 0.0
    for _, dy in raw_resampled:
        energy_total += abs(dy)
        raw_energy.append(energy_total)
    energy_total = energy_total or 1.0

    ref_cum_x: List[float] = []
    acc_x = 0.0
    for dx in ref_dx:
        acc_x += dx
        ref_cum_x.append(acc_x)
    final_ref_x = ref_cum_x[-1] if ref_cum_x else 0.0

    fitted: List[Tuple[float, float, float]] = []
    out_cum_x = 0.0

    for i, (raw_dx, raw_dy) in enumerate(raw_resampled):
        weight_y = abs(raw_dy) / total_raw_y
        dy = round(weight_y * total_ref_y * scale_y, 3)

        if weak_horizontal:
            progress = raw_energy[i] / energy_total
            target_cum_x = final_ref_x * progress * h_strength
            dx = round((target_cum_x - out_cum_x) * scale_x, 3)
        else:
            weight_x = abs(raw_dx) / (sum(abs(x) for x, _ in raw_resampled) or 1e-6)
            dx = round(weight_x * ref_sum_x * h_strength * scale_x, 3)

        out_cum_x += dx
        fitted.append((dx, dy, ref_delay[i]))

    fitted = _trim_outlier_tail(fitted, reference)
    return _fix_total_drift(
        fitted,
        final_ref_x * scale_x * h_strength,
        total_ref_y * scale_y,
    )


def _f(value: object) -> float:
    return float(value)


def build_recoil_steps(
    raw_points: Sequence[dict],
    delay_ms: int = 90,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    invert_x: bool = True,
    invert_y: bool = True,
    export_mode: str = "canonical",
    reference_steps: Sequence[Tuple[float, float, float]] | None = None,
    horizontal_strength: float = 1.0,
) -> Dict[str, object]:
    export = (export_mode or "canonical").strip().lower()
    if export == "laser_fit":
        if not reference_steps:
            raise ValueError("reference_weapon is required for laser_fit export mode.")
        steps_seconds = laser_fit_steps(
            raw_points,
            reference_steps,
            scale_x=scale_x,
            scale_y=scale_y,
            invert_x=invert_x,
            invert_y=invert_y,
            horizontal_strength=horizontal_strength,
        )
        steps_ms = [(x, y, int(round(d * 1000))) for x, y, d in steps_seconds]
        pattern_text = "\n".join(f"{x},{y},{d}" for x, y, d in steps_seconds)
        return {
            "pattern_text": pattern_text,
            "steps_ms": steps_ms,
            "steps_seconds": steps_seconds,
            "export_mode": "laser_fit",
        }

    points = normalize_points(raw_points)
    validate_points(points)
    steps_ms: List[Tuple[float, float, int]] = []
    steps_seconds: List[Tuple[float, float, float]] = []

    sign_x = -1.0 if invert_x else 1.0
    sign_y = -1.0 if invert_y else 1.0

    for idx in range(1, len(points)):
        prev = points[idx - 1]
        curr = points[idx]
        dx = (curr.x - prev.x) * scale_x * sign_x
        dy = (curr.y - prev.y) * scale_y * sign_y
        dx = round(dx, 3)
        dy = round(dy, 3)
        steps_ms.append((dx, dy, int(delay_ms)))
        steps_seconds.append((dx, dy, round(delay_ms / 1000.0, 3)))

    if export_mode == "engine_steps":
        pattern_text = "\n".join(f"{x},{y},{d}" for x, y, d in steps_ms)
    else:
        pattern_text = "\n".join(f"{x},{y},{d}" for x, y, d in steps_seconds)

    return {
        "pattern_text": pattern_text,
        "steps_ms": steps_ms,
        "steps_seconds": steps_seconds,
        "export_mode": export_mode if export_mode == "engine_steps" else "canonical",
    }


def _format_weapon_block(weapon_name: str, steps_seconds: Sequence[Tuple[float, float, float]]) -> str:
    rows = [f"            ({x}, {y}, {d})," for x, y, d in steps_seconds]
    if rows:
        rows[-1] = rows[-1].rstrip(",")
    body = "\n".join(rows)
    return f"        self.{weapon_name} = [\n{body}\n        ]"


def _make_backup(target: Path) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = target.with_suffix(target.suffix + f".{stamp}.bak")
    shutil.copy2(target, backup)
    return backup


def append_weapon_data(
    repo_root: Path,
    game_id: str,
    weapon_name: str,
    steps_seconds: Sequence[Tuple[float, float, float]],
    overwrite: bool = True,
) -> Dict[str, str]:
    if game_id not in GAME_FILE_MAP:
        raise ValueError(f"Unsupported game '{game_id}'.")
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", weapon_name):
        raise ValueError("Weapon name must be snake_case style.")
    if not steps_seconds:
        raise ValueError("No steps to append.")

    target = repo_root / "Recoil" / "games" / GAME_FILE_MAP[game_id]
    if not target.is_file():
        raise FileNotFoundError(f"Game data file not found: {target}")

    source = target.read_text(encoding="utf-8")
    backup_path = _make_backup(target)
    weapon_block = _format_weapon_block(weapon_name, steps_seconds)

    existing_pattern = re.compile(
        rf"^\s*self\.{re.escape(weapon_name)}\s*=\s*\[(?:.|\n)*?^\s*\]",
        re.MULTILINE,
    )
    if existing_pattern.search(source):
        if not overwrite:
            raise ValueError(f"Weapon '{weapon_name}' already exists. Enable overwrite.")
        updated = existing_pattern.sub(weapon_block, source, count=1)
        action = "updated"
    else:
        if source.rfind("]") == -1:
            raise RuntimeError("Failed to locate class weapon list anchor.")
        updated = source.rstrip() + "\n\n" + weapon_block + "\n"
        action = "appended"

    target.write_text(updated, encoding="utf-8")
    return {"action": action, "backup_path": str(backup_path), "target_file": str(target)}
