"""Model class catalog for UI (what the YOLO model can detect)."""

from __future__ import annotations

from pathlib import Path

from app.ai.class_names import class_details, class_name_list, resolve_class_names
from app.ai.team_target import enemy_class_for_team, has_ct_t_classes


def class_info_for_path(model_path: str) -> dict:
    path = Path((model_path or '').strip())
    if not path.is_file():
        return {
            'model_classes': [],
            'model_class_details': [],
            'has_ct_t': False,
        }

    names = resolve_class_names(path)
    labels = class_name_list(names)
    return {
        'model_classes': labels,
        'model_class_details': class_details(names),
        'has_ct_t': has_ct_t_classes(labels),
    }


def apply_team_to_player_class(config: dict) -> dict[str, str]:
    """Return config updates when ai_my_team should drive ai_player_class."""
    team = str(config.get('ai_my_team') or '').strip().lower()
    if team not in {'ct', 't'}:
        return {}
    path = str(config.get('ai_model_path') or '').strip()
    if not path:
        return {}
    labels = class_info_for_path(path).get('model_classes', [])
    enemy = enemy_class_for_team(team, labels)
    if not enemy:
        return {}
    return {'ai_player_class': enemy}
