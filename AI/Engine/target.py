"""Target selection from YOLO output (FOV filter + nearest to center)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from AI.Engine.capture import DetectionRegion
from AI.Engine.settings import AiSettings


@dataclass
class Prediction:
    x_min: float
    y_min: float
    width: float
    height: float
    confidence: float
    class_id: int
    screen_center_x: float
    screen_center_y: float
    detection_box: tuple[float, float, float, float]


class TargetSelector:
    def __init__(self, settings: AiSettings) -> None:
        self._settings = settings
        self._sticky_target: Prediction | None = None
        self._frames_without_target = 0
        self._max_frames_without = 3

    def reset_sticky(self) -> None:
        self._sticky_target = None
        self._frames_without_target = 0

    def _matches_detection_class(
        self,
        class_name: str,
        class_id: int,
        player_label: str,
        head_label: str,
        *,
        exclude_friendly: bool = False,
    ) -> tuple[bool, str]:
        """Filter detections by enemy body/head class (or exclude friendly team)."""
        if not player_label and not head_label:
            return True, 'player'

        name_str = str(class_name)
        player_str = str(player_label) if player_label else ''
        head_str = str(head_label) if head_label else ''

        def _name_matches(label: str) -> bool:
            if not label:
                return False
            if name_str == label or str(class_id) == label:
                return True
            if len(label) > 1 and not label.isdigit():
                return label.lower() in name_str.lower()
            return False

        if exclude_friendly and player_str:
            if _name_matches(player_str):
                return False, ''
            if head_str and _name_matches(head_str):
                return False, ''
            return True, 'player'

        if player_str and _name_matches(player_str):
            return True, 'player'
        if head_str and _name_matches(head_str):
            return True, 'head'
        return False, ''

    def select(
        self,
        output: np.ndarray,
        region: DetectionRegion,
        image_size: int,
        num_detections: int,
        num_classes: int = 1,
        *,
        class_names: dict[int, str] | None = None,
        player_label: str = '',
        head_label: str = '',
        player_y_offset: int = 0,
        min_confidence: float | None = None,
        fov_size: float | None = None,
        exclude_friendly: bool = False,
    ) -> Prediction | None:
        if min_confidence is not None:
            min_conf = float(min_confidence)
        else:
            min_conf = float(self._settings.sliders['AI Minimum Confidence']) / 100.0
        fov = float(fov_size) if fov_size is not None else float(self._settings.sliders['FOV Size'])
        fov_min_x = (image_size - fov) / 2.0
        fov_max_x = (image_size + fov) / 2.0
        fov_min_y = (image_size - fov) / 2.0
        fov_max_y = (image_size + fov) / 2.0

        candidates: list[Prediction] = []
        center_x = image_size / 2.0
        center_y = image_size / 2.0

        for i in range(min(num_detections, output.shape[2])):
            x_center = float(output[0, 0, i])
            y_center = float(output[0, 1, i])
            width = float(output[0, 2, i])
            height = float(output[0, 3, i])

            if num_classes == 1:
                confidence = float(output[0, 4, i])
                class_id = 0
            else:
                class_scores = output[0, 4:4 + num_classes, i]
                class_id = int(np.argmax(class_scores))
                confidence = float(class_scores[class_id])

            if confidence < min_conf:
                continue

            class_name = (class_names or {}).get(class_id, str(class_id))
            if player_label or head_label:
                is_target, target_type = self._matches_detection_class(
                    class_name, class_id, player_label, head_label,
                    exclude_friendly=exclude_friendly,
                )
                if not is_target:
                    continue
            else:
                target_type = 'player'

            x_min = x_center - width / 2
            y_min = y_center - height / 2
            x_max = x_center + width / 2
            y_max = y_center + height / 2

            if x_min < fov_min_x or x_max > fov_max_x or y_min < fov_min_y or y_max > fov_max_y:
                continue

            aim_x = x_center
            aim_y = y_center
            if target_type == 'player' and player_y_offset:
                aim_y = y_min + float(player_y_offset)

            pred = Prediction(
                x_min=x_min,
                y_min=y_min,
                width=width,
                height=height,
                confidence=confidence,
                class_id=class_id,
                screen_center_x=region.left + aim_x,
                screen_center_y=region.top + aim_y,
                detection_box=(region.left + x_min, region.top + y_min, width, height),
            )
            candidates.append(pred)

        if not candidates:
            self._handle_sticky_loss()
            return self._sticky_target if self._settings.toggles['Sticky Aim'] else None

        def _center_dist(pred: Prediction) -> float:
            cx = pred.x_min + pred.width / 2.0
            cy = pred.y_min + pred.height / 2.0
            return (cx - center_x) ** 2 + (cy - center_y) ** 2

        best = min(candidates, key=_center_dist)
        return self._apply_sticky(best, candidates)

    def _handle_sticky_loss(self) -> None:
        if not self._settings.toggles['Sticky Aim']:
            self._sticky_target = None
            return
        self._frames_without_target += 1
        if self._frames_without_target > self._max_frames_without:
            self._sticky_target = None

    def _apply_sticky(self, best: Prediction, candidates: list[Prediction]) -> Prediction | None:
        if not self._settings.toggles['Sticky Aim']:
            return best

        threshold = float(self._settings.sliders['Sticky Aim Threshold'])
        threshold_sq = threshold * threshold

        if self._sticky_target is not None:
            matched = None
            min_dist = float('inf')
            for candidate in candidates:
                dx = candidate.screen_center_x - self._sticky_target.screen_center_x
                dy = candidate.screen_center_y - self._sticky_target.screen_center_y
                dist_sq = dx * dx + dy * dy
                if dist_sq < min_dist and dist_sq < threshold_sq:
                    min_dist = dist_sq
                    matched = candidate
            if matched is not None:
                self._sticky_target = matched
                self._frames_without_target = 0
                return matched
            self._handle_sticky_loss()
            if self._sticky_target is not None and self._frames_without_target <= self._max_frames_without:
                return self._sticky_target

        self._sticky_target = best
        self._frames_without_target = 0
        return best
