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
    from PIL import Image, ImageSequence
except Exception:  # pragma: no cover
    Image = None
    ImageSequence = None


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


def detect_points_and_preview(image_bytes: bytes) -> Dict[str, object]:
    frames = _collect_frames(image_bytes)
    preview = frames[0].copy()
    points = _auto_suggest_points(frames)
    frame_data_urls = [_to_data_url_png(frame) for frame in frames]
    return {
        "width": preview.width,
        "height": preview.height,
        "preview_data_url": _to_data_url_png(preview),
        "frame_data_urls": frame_data_urls,
        "frame_count": len(frame_data_urls),
        "suggested_points": [{"x": x, "y": y} for x, y in points],
    }


def build_recoil_steps(
    raw_points: Sequence[dict],
    delay_ms: int = 90,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    invert_x: bool = True,
    invert_y: bool = True,
    export_mode: str = "canonical",
) -> Dict[str, object]:
    points = normalize_points(raw_points)
    validate_points(points)
    steps_ms: List[Tuple[float, float, int]] = []
    steps_seconds: List[Tuple[float, float, float]] = []

    sign_x = -1.0 if invert_x else 1.0
    sign_y = -1.0 if invert_y else 1.0

    if export_mode == "engine_steps":
        for idx in range(1, len(points)):
            prev = points[idx - 1]
            curr = points[idx]
            dx = (curr.x - prev.x) * scale_x * sign_x
            dy = (curr.y - prev.y) * scale_y * sign_y
            dx = round(dx, 3)
            dy = round(dy, 3)
            steps_ms.append((dx, dy, int(delay_ms)))
            steps_seconds.append((dx, dy, round(delay_ms / 1000.0, 3)))
        pattern_text = "\n".join(f"{x},{y},{d}" for x, y, d in steps_ms)
        return {
            "pattern_text": pattern_text,
            "steps_ms": steps_ms,
            "steps_seconds": steps_seconds,
            "export_mode": export_mode,
        }

    # Canonical 1:1 mode: absolute points referenced from first bullet impact.
    origin_x = points[0].x
    origin_y = points[0].y
    for point in points:
        x = (point.x - origin_x) * scale_x * sign_x
        y = (point.y - origin_y) * scale_y * sign_y
        x = round(x, 3)
        y = round(y, 3)
        steps_ms.append((x, y, int(delay_ms)))
        steps_seconds.append((x, y, round(delay_ms / 1000.0, 3)))

    pattern_text = "\n".join(f"{x},{y},{d}" for x, y, d in steps_seconds)
    return {
        "pattern_text": pattern_text,
        "steps_ms": steps_ms,
        "steps_seconds": steps_seconds,
        "export_mode": "canonical",
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
