"""Convert detector output to aim/trigger targets."""

from __future__ import annotations

import math

from app.ai.types import Prediction

# Fraction from top of body bbox → aim height.
_AIM_Y_FRACTION: dict[str, float] = {
    'head': 0.40,
    'body': 0.40,
    'neck': 0.28,
    'center': 0.50,
}
# Horizontal offset from bbox center, as fraction of bbox width (+ = right).
_AIM_X_OFFSET: dict[str, float] = {
    'head': 0.075,  # 5% + 1.5% + 1% fine-tune
    'body': 0.0,
    'neck': 0.0,
    'center': 0.0,
}

# Legacy config / UI values.
_AIM_POINT_ALIASES: dict[str, str] = {
    'chest': 'head',
}


def normalize_aim_point(aim_point: str) -> str:
    point = (aim_point or 'head').strip().lower()
    return _AIM_POINT_ALIASES.get(point, point)


def resolve_head_class(
    head_class: str,
    model_names: dict[int, str] | None,
) -> str:
    manual = head_class.strip()
    if manual:
        return manual
    if not model_names:
        return ''
    for name in model_names.values():
        if str(name).lower() == 'head':
            return str(name)
    return ''


def _matches_class(class_name: str, class_id: int, label: str) -> bool:
    text = label.strip()
    if not text:
        return False
    if text == str(class_id):
        return True
    cname = class_name.strip().lower()
    lname = text.lower()
    if lname == cname:
        return True
    # CS2: "T" must not match "CT" (substring bug).
    if len(lname) <= 3 and len(cname) <= 3:
        return False
    if len(lname) >= 3 and lname in cname:
        return True
    if len(cname) >= 3 and cname in lname:
        return True
    return False


def aim_y_from_bbox(
    y1: float,
    y2: float,
    *,
    aim_point: str,
    is_head_class: bool,
) -> float:
    if is_head_class:
        return (y1 + y2) / 2.0
    frac = _AIM_Y_FRACTION.get(normalize_aim_point(aim_point), _AIM_Y_FRACTION['head'])
    height = max(float(y2) - float(y1), 1.0)
    return float(y1) + height * frac


def aim_x_from_bbox(
    x1: float,
    x2: float,
    *,
    aim_point: str,
    is_head_class: bool,
) -> float:
    center = (float(x1) + float(x2)) / 2.0
    if is_head_class:
        return center
    width = max(float(x2) - float(x1), 1.0)
    off = _AIM_X_OFFSET.get(normalize_aim_point(aim_point), 0.0)
    return center + width * off


def predictions_from_detections(
    detections: list[dict[str, float | int | str]],
    image_size: int,
    *,
    player_label: str = '',
    head_class: str = '',
    aim_point: str = 'head',
    model_names: dict[int, str] | None = None,
) -> list[Prediction]:
    center_x = image_size / 2.0
    center_y = image_size / 2.0
    targets: list[Prediction] = []
    player_filter = player_label.strip()
    head_filter = resolve_head_class(head_class, model_names)
    point = normalize_aim_point(aim_point)

    for det in detections:
        class_name = str(det.get('class_name', ''))
        class_id = int(det['class_id'])
        is_head = bool(head_filter) and _matches_class(class_name, class_id, head_filter)
        is_player = bool(player_filter) and _matches_class(class_name, class_id, player_filter)

        if is_head:
            pass
        elif player_filter:
            if not is_player:
                continue
        elif head_filter:
            continue
        else:
            is_player = True

        x1 = float(det['x1'])
        y1 = float(det['y1'])
        x2 = float(det['x2'])
        y2 = float(det['y2'])
        aim_x = aim_x_from_bbox(x1, x2, aim_point=point, is_head_class=is_head)
        aim_y = aim_y_from_bbox(y1, y2, aim_point=point, is_head_class=is_head)
        dist = math.hypot(aim_x - center_x, aim_y - center_y)
        targets.append(
            Prediction(
                confidence=float(det['confidence']),
                image_dist=dist,
                screen_center_x=aim_x,
                screen_center_y=aim_y,
                is_head=is_head,
            )
        )
    return targets
